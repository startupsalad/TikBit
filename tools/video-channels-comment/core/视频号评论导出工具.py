#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频号评论导出工具
------------------
从「视频号助手」后台（channels.weixin.qq.com）批量导出你自己视频号所有视频的评论。
走的是你已登录的官方后台，合规、不碰灰色地带；评论数据直接从页面读取，无需破解接口。

前置条件：
  1. 用「调试模式」启动 Chrome（保留你的登录）：
     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \
       --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-debug" &
  2. 在这个 Chrome 里扫码登录 视频号助手，并打开「互动管理 → 评论」页面。

用法：
  python3 视频号评论导出工具.py                    # 抓全部有评论的视频
  python3 视频号评论导出工具.py --max 20           # 只抓前20个有评论的视频
  python3 视频号评论导出工具.py --include-zero     # 连0评论视频也列进表（默认跳过）

产物（存到知识库根目录 视频号评论导出/ 下，带时间戳）：
  - 视频号评论_<时间>.md    人可读的总表（视频 | 评论者 | 内容 | 时间 | 点赞 | 作者是否回复）
  - 视频号评论_<时间>.csv   Excel 可打开
  - 视频号评论_<时间>.json  完整结构化数据（含嵌套回复）

限制：只能抓「你自己账号」的视频评论，抓不了别人的视频。

依赖：需要 playwright 库（AI 会自动帮你装）
"""
import sys, os, time, json, csv, argparse
from datetime import datetime

CDP_URL = "http://localhost:9222"
COMMENT_URL = "https://channels.weixin.qq.com/platform/interaction/comment"
FRAME_HINT = "/micro/interaction/comment"

# ---- 页面内 JS：加载全部视频列表 ----
JS_LOAD_ALL_VIDEOS = r"""
async ()=>{
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const sc=document.querySelector('.feeds-container')||document.querySelector('.scroll-list__wrp');
  if(!sc) return {count:0, note:'no scroll container'};
  let prev=-1, stable=0;
  for(let i=0;i<80 && stable<3;i++){
    sc.scrollTop = sc.scrollHeight;
    await sleep(600);
    const n=document.querySelectorAll('.comment-feed-wrap').length;
    if(n===prev) stable++; else stable=0;
    prev=n;
  }
  return {count: document.querySelectorAll('.comment-feed-wrap').length};
}
"""

# ---- 页面内 JS：读取视频列表元信息（标题/日期/评论数） ----
JS_VIDEO_LIST = r"""
()=>{
  return [...document.querySelectorAll('.comment-feed-wrap')].map((w,i)=>{
    const t=(w.querySelector('.feed-title')||{}).innerText||'';
    const d=(w.querySelector('.feed-time')||{}).innerText||'';
    const c=(w.querySelector('.feed-comment-total')||{}).innerText||'';
    const num=(c.match(/\d+/)||[0])[0];
    return {index:i, title:t.trim().replace(/\s+/g,' '), date:d.trim(), count:parseInt(num)||0};
  });
}
"""

# ---- 页面内 JS：滚动评论面板加载全部评论 ----
JS_LOAD_COMMENTS = r"""
async ()=>{
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  // 评论面板的滚动容器：包含 .comment-item 的可滚动祖先
  const anchor=document.querySelector('.comment-item');
  let sc=null, cur=anchor;
  while(cur){const o=getComputedStyle(cur).overflowY; if((o==='auto'||o==='scroll')&&cur.scrollHeight>cur.clientHeight){sc=cur;break;} cur=cur.parentElement;}
  // 展开被折叠的回复
  const clickExpand=()=>{document.querySelectorAll('*').forEach(e=>{if(e.children.length===0&&/展开|条回复|查看更多回复/.test(e.textContent)&&e.textContent.length<20){try{e.click();}catch(_){}}});};
  let prev=-1, stable=0;
  for(let i=0;i<40 && stable<3;i++){
    if(sc) sc.scrollTop=sc.scrollHeight;
    clickExpand();
    await sleep(400);
    const n=document.querySelectorAll('.comment-item').length;
    if(n===prev) stable++; else stable=0;
    prev=n;
  }
  return {items: document.querySelectorAll('.comment-item').length};
}
"""

# ---- 页面内 JS：结构化提取当前视频的评论 ----
JS_EXTRACT = r"""
()=>{
  const textOf=(el)=>{
    if(!el) return '';
    const clone=el.cloneNode(true);
    clone.querySelectorAll('img').forEach(img=>{img.replaceWith(document.createTextNode(img.getAttribute('alt')||''));});
    return clone.innerText.replace(/\s+/g,' ').trim();
  };
  const q=(el,s)=>el?el.querySelector(s):null;
  const topItems=[...document.querySelectorAll('.comment-item')].filter(it=>!it.parentElement.closest('.comment-reply-list'));
  return topItems.map(it=>{
    const main=q(it,'.comment-item-main')||it;
    const user=((q(main,'.comment-user-name')||{}).innerText||'').trim();
    const time=((q(main,'.comment-time')||{}).innerText||'').trim();
    const content=textOf(q(main,'.comment-content'));
    const likes=(((q(main,'.like-action .action-count')||{}).innerText)||'0').trim()||'0';
    const replies=[...it.querySelectorAll('.comment-reply-list .comment-item')].map(r=>({
      user:((q(r,'.comment-user-name')||{}).innerText||'').trim(),
      time:((q(r,'.comment-time')||{}).innerText||'').trim(),
      content:textOf(q(r,'.comment-content')),
      isAuthor: /作者/.test((r.innerText||'').slice(0,50)),
      likes:(((q(r,'.like-action .action-count')||{}).innerText)||'0').trim()||'0'
    }));
    return {user, time, content, likes, replies};
  });
}
"""


def get_frame(page):
    for f in page.frames:
        if FRAME_HINT in f.url:
            return f
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="最多抓多少个有评论的视频（0=全部）")
    ap.add_argument("--include-zero", action="store_true", help="把0评论视频也列进表")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 未安装 playwright。请先运行： pip3 install playwright --user")
        sys.exit(1)

    with sync_playwright() as p:
        try:
            b = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"❌ 连不上 Chrome 调试端口 {CDP_URL}。请确认 Chrome 已用 --remote-debugging-port=9222 启动。\n   {e}")
            sys.exit(1)

        # 找到视频号助手页面
        page = None
        for ctx in b.contexts:
            for pg in ctx.pages:
                if "channels.weixin.qq.com" in pg.url:
                    page = pg; break
            if page: break
        if not page:
            print("❌ 没找到已打开的视频号助手页面，请先在 Chrome 里打开 channels.weixin.qq.com")
            sys.exit(1)
        page.bring_to_front()

        # 确保在评论页
        if "interaction/comment" not in page.url:
            print("→ 正在导航到评论页…")
            page.goto(COMMENT_URL, wait_until="domcontentloaded")
            time.sleep(5)

        frame = get_frame(page)
        if not frame:
            print("→ 评论 iframe 未就绪，等待…")
            time.sleep(4)
            frame = get_frame(page)
        if not frame:
            print("❌ 找不到评论内容 iframe。请确认页面停在「互动管理 → 评论」。")
            sys.exit(1)

        print("→ 加载全部视频列表（滚动中）…")
        r = frame.evaluate(JS_LOAD_ALL_VIDEOS)
        videos = frame.evaluate(JS_VIDEO_LIST)
        total = len(videos)
        with_comments = [v for v in videos if v["count"] > 0]
        print(f"→ 共 {total} 个视频，其中 {len(with_comments)} 个有评论。")

        targets = with_comments if not args.include_zero else videos
        if args.max and args.max > 0:
            targets = targets[:args.max]

        results = []
        for n, v in enumerate(targets, 1):
            if v["count"] == 0 and not args.include_zero:
                continue
            print(f"  [{n}/{len(targets)}] 抓取：{v['title'][:30]}…（评论数 {v['count']}）")
            try:
                frame.locator(".comment-feed-wrap").nth(v["index"]).dispatch_event("click")
            except Exception as e:
                print(f"      ⚠️ 点击失败，跳过：{e}")
                continue
            time.sleep(1.5)
            try:
                frame.evaluate(JS_LOAD_COMMENTS)
            except Exception:
                pass
            time.sleep(0.5)
            try:
                comments = frame.evaluate(JS_EXTRACT)
            except Exception as e:
                print(f"      ⚠️ 提取失败：{e}")
                comments = []
            results.append({
                "video_title": v["title"],
                "video_date": v["date"],
                "comment_count_shown": v["count"],
                "comments": comments,
            })

        # ---- 导出 ----
        # 输出到知识库根目录的 视频号评论导出/ 文件夹
        # 优先级：环境变量 OBSIDIAN_VAULT > 当前目录（含 CLAUDE.md 视为知识库根）> 当前目录
        if os.getenv("OBSIDIAN_VAULT"):
            vault_root = os.getenv("OBSIDIAN_VAULT")
        elif os.path.exists(os.path.join(os.getcwd(), "CLAUDE.md")):
            vault_root = os.getcwd()
        else:
            vault_root = os.getcwd()
        outdir = os.path.join(vault_root, "视频号评论导出")
        os.makedirs(outdir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        base = os.path.join(outdir, f"视频号评论_{ts}")

        # JSON
        with open(base + ".json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # CSV（打平：一行一条顶层评论）
        with open(base + ".csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["视频标题", "视频日期", "评论者", "评论内容", "评论时间", "点赞", "作者是否回复", "作者回复内容"])
            for r in results:
                for c in r["comments"]:
                    author_replies = [rp for rp in c["replies"] if rp["isAuthor"]]
                    replied = "是" if author_replies else "否"
                    reply_txt = " / ".join(rp["content"] for rp in author_replies)
                    w.writerow([r["video_title"], r["video_date"], c["user"], c["content"], c["time"], c["likes"], replied, reply_txt])

        # Markdown 总表
        total_comments = sum(len(r["comments"]) for r in results)
        lines = [
            f"# 视频号评论导出 · {ts}",
            "",
            f"- 视频总数：{total}（有评论 {len(with_comments)}）",
            f"- 本次抓取视频：{len(results)} 个",
            f"- 抓到顶层评论：{total_comments} 条",
            "",
            "> 说明：只含你自己视频号的评论。表格按视频分组，作者回复折叠在「作者回复」列。",
            "",
        ]
        for r in results:
            if not r["comments"]:
                continue
            lines.append(f"## {r['video_title']}")
            lines.append(f"*{r['video_date']} · {len(r['comments'])} 条评论*")
            lines.append("")
            lines.append("| 评论者 | 评论内容 | 时间 | 点赞 | 作者回复 |")
            lines.append("|---|---|---|---|---|")
            for c in r["comments"]:
                author_replies = [rp["content"] for rp in c["replies"] if rp["isAuthor"]]
                reply_txt = "<br>".join(author_replies) if author_replies else "—"
                content = (c["content"] or "").replace("|", "\\|").replace("\n", " ")
                reply_txt = reply_txt.replace("|", "\\|")
                lines.append(f"| {c['user']} | {content} | {c['time']} | {c['likes']} | {reply_txt} |")
            lines.append("")
        with open(base + ".md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"\n✅ 完成！抓取 {len(results)} 个视频、{total_comments} 条评论。")
        print(f"   Markdown: {base}.md")
        print(f"   CSV:      {base}.csv")
        print(f"   JSON:     {base}.json")


if __name__ == "__main__":
    main()
