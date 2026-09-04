#!/usr/bin/env node
/* ============================================================================
 * TikBit AI 工作台 · 视频号评论导出工具 · 核心安装器 install-core.js
 * ----------------------------------------------------------------------------
 * 跨平台一份逻辑，让用户的 AI 调用来安装工具。
 * 干的活：
 *   1) 建目录 ~/.claude/channels-comment/
 *   2) 拷 视频号评论导出工具.py 进去
 *   3) 往全局 + 各 Obsidian 知识库的 CLAUDE.md（Claude 读）和 AGENTS.md（GPT 读）追加「视频号评论导出」指令块
 *      （教 AI 何时/如何调用 + 检查依赖 playwright）—— 双模型：两个大脑都能调这个外部脚本
 *
 * 用法：node install-core.js <视频号评论导出工具.py的绝对路径>
 * 卸载：node install-core.js --uninstall
 * ========================================================================== */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const TOOL_DIR = path.join(HOME, '.claude', 'channels-comment');
const TOOL_FILE = 'channels-comment-export.py';
const GLOBAL_CLAUDE = path.join(HOME, '.claude', 'CLAUDE.md');   // 全局·Claude 读
const GLOBAL_CODEX = path.join(HOME, '.codex', 'AGENTS.md');     // 全局·GPT(Codex) 读
const OBSIDIAN_BASE = path.join(HOME, 'Library', 'Mobile Documents', 'iCloud~md~obsidian', 'Documents');

// 收集要写指令块的所有说明书文件：全局两份 + 每个知识库的 CLAUDE.md 和 AGENTS.md。
// 双模型：Claude 读 CLAUDE.md、GPT 读 AGENTS.md，本工具是外部脚本、两个大脑都能调，故两份都写。
// 判定"是知识库"：该文件夹有 CLAUDE.md 或 AGENTS.md 任一即算（缺的那份会补建）。
function collectMdTargets() {
  const targets = [GLOBAL_CLAUDE, GLOBAL_CODEX];
  if (fs.existsSync(OBSIDIAN_BASE)) {
    for (const name of fs.readdirSync(OBSIDIAN_BASE)) {
      const dir = path.join(OBSIDIAN_BASE, name);
      try {
        if (!fs.statSync(dir).isDirectory()) continue;
        const cmd = path.join(dir, 'CLAUDE.md');
        const amd = path.join(dir, 'AGENTS.md');
        if (fs.existsSync(cmd) || fs.existsSync(amd)) { targets.push(cmd, amd); }
      } catch (_) {}
    }
  }
  return targets;
}

const C = { r: '\x1b[31m', g: '\x1b[32m', y: '\x1b[33m', b: '\x1b[36m', n: '\x1b[0m' };

// ★ MD_ID 是品牌无关的内部 ID，永不改。清理正则只锚定它，不锚品牌名、不锚标题文字，
//   这样带任何历史品牌名的旧块（旧品牌名/新品牌名/未来任何名字）都能被认出来正常替换/删除。
const MD_ID = 'CHANNELS-COMMENT';
const MD_BEGIN = `<!-- ${MD_ID}-BEGIN (这个块由「TikBit AI 工作台·视频号评论导出工具」自动管理，请勿手动编辑) -->`;
const MD_END = `<!-- ${MD_ID}-END -->`;
// 开头那段可选的标题捕获是**旧版布局兼容**：老版本把「## 🎥 视频号评论导出工具」写在 BEGIN 之外，
// 只吃 BEGIN…END 会把标题行留成孤儿 → 老用户每重装一次多一行重复标题、卸载也删不掉。
const mdRe = () => new RegExp('(?:##\\s*🎥\\s*视频号评论导出工具\\s*\\n)?<!--\\s*' + MD_ID + '-BEGIN[\\s\\S]*?' + MD_ID + '-END\\s*-->', 'g');

const CLAUDE_BLOCK = `
${MD_BEGIN}
## 🎥 视频号评论导出工具

**核心能力**：批量导出用户自己视频号后台的所有评论（评论者、内容、时间、点赞、作者回复），生成 Markdown/CSV/JSON 三种格式。

**触发场景**：
- 用户说「导出我视频号的评论」「抓取视频号评论」「分析我视频号评论」
- 用户问「能不能导出视频号评论」「我想看视频号的评论数据」

**使用前提（你需要先检查/引导）**：
1. **Chrome 用调试模式启动**（保留登录态）：
   \`\`\`bash
   # Mac:
   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-debug" &
   # Windows:
   start chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\\chrome-debug"
   \`\`\`
2. **在这个 Chrome 里登录视频号助手**（channels.weixin.qq.com），并打开「互动管理 → 评论」页面，停在这个页面。
3. **playwright 库已安装**（见下方依赖检查）

**调用方式**（当上述前提都满足时）：
\`\`\`bash
python3 ~/.claude/channels-comment/${TOOL_FILE}
# 或带参数：
python3 ~/.claude/channels-comment/${TOOL_FILE} --max 20        # 只抓前20个视频
python3 ~/.claude/channels-comment/${TOOL_FILE} --include-zero  # 连0评论视频也列进表
\`\`\`

**依赖检查与自动安装**：
工具依赖 \`playwright\` 库。调用前先检查：
\`\`\`bash
python3 -c "import playwright" 2>/dev/null && echo "OK" || echo "NOT_INSTALLED"
\`\`\`
如果输出 \`NOT_INSTALLED\`，自动安装（用 pip 或 pip3）：
\`\`\`bash
pip3 install playwright --user
\`\`\`
安装后无需再跑 \`playwright install\`（工具通过 CDP 连已打开的 Chrome，不需要下载浏览器）。

**产物位置**：\`<知识库根目录>/视频号评论导出/\` 下，带时间戳的三个文件（.md / .csv / .json）

**限制说明**：
- 只能导出用户**自己账号**的视频评论（视频号没开放接口，别人的评论锁在微信客户端里）
- 走的是官方后台，完全合规，不碰灰色地带

**引导用户的话术**（当用户问能不能导出时）：
"可以的！我能帮你把视频号后台的所有评论导出成表格，方便你分析读者关注什么、找选题。需要先用调试模式开个 Chrome 并登录视频号助手，我来教你三步搞定…"

${MD_END}
`;

function install(scriptPath) {
  if (!scriptPath || !fs.existsSync(scriptPath)) {
    console.error(`${C.r}错误：找不到脚本文件 ${scriptPath}${C.n}`);
    console.error('用法：node install-core.js <视频号评论导出工具.py的绝对路径>');
    process.exit(1);
  }

  console.log(`${C.b}======== 视频号评论导出工具 · 安装中 ========${C.n}`);

  // 1) 建目录
  if (!fs.existsSync(TOOL_DIR)) {
    fs.mkdirSync(TOOL_DIR, { recursive: true });
    console.log(`${C.g}✓${C.n} 创建 ${TOOL_DIR}`);
  }

  // 2) 拷脚本
  const dest = path.join(TOOL_DIR, TOOL_FILE);
  fs.copyFileSync(scriptPath, dest);
  if (process.platform !== 'win32') fs.chmodSync(dest, 0o755);
  console.log(`${C.g}✓${C.n} 拷贝脚本 → ${dest}`);

  // 3) 写指令块到 CLAUDE.md（Claude）+ AGENTS.md（GPT），全局 + 各知识库
  const targets = collectMdTargets();

  targets.forEach(md => {
    if (!fs.existsSync(md)) {
      fs.mkdirSync(path.dirname(md), { recursive: true });
      fs.writeFileSync(md, CLAUDE_BLOCK, 'utf8');
      console.log(`${C.g}✓${C.n} 新建 ${md}`);
      return;
    }
    let content = fs.readFileSync(md, 'utf8');
    const re = mdRe();
    if (re.test(content)) {
      re.lastIndex = 0;
      content = content.replace(re, CLAUDE_BLOCK.trim());
      console.log(`${C.y}↻${C.n} 更新 ${md}`);
    } else {
      content += '\n' + CLAUDE_BLOCK;
      console.log(`${C.g}✓${C.n} 追加 ${md}`);
    }
    fs.writeFileSync(md, content, 'utf8');
  });

  console.log(`${C.g}========================================${C.n}`);
  console.log(`${C.g}  🎥 视频号评论导出工具安装成功！${C.n}`);
  console.log(`${C.g}========================================${C.n}`);
  console.log(`\n  ${C.b}下一步：${C.n}`);
  console.log(`  1. 关掉现有 Chrome，用调试模式重开（见上面命令）`);
  console.log(`  2. 在这个 Chrome 里登录 channels.weixin.qq.com，点「互动管理→评论」`);
  console.log(`  3. 回 Obsidian 跟 AI 说「导出我视频号的评论」即可\n`);
}

function uninstall() {
  console.log(`${C.y}======== 卸载视频号评论导出工具 ========${C.n}`);
  if (fs.existsSync(TOOL_DIR)) {
    fs.rmSync(TOOL_DIR, { recursive: true });
    console.log(`${C.g}✓${C.n} 删除 ${TOOL_DIR}`);
  }
  const targets = collectMdTargets();
  targets.forEach(md => {
    if (!fs.existsSync(md)) return;
    let content = fs.readFileSync(md, 'utf8');
    const re = mdRe();
    if (re.test(content)) {
      re.lastIndex = 0;
      content = content.replace(re, '').replace(/\n{3,}/g, '\n\n').trim() + '\n';
      fs.writeFileSync(md, content, 'utf8');
      console.log(`${C.g}✓${C.n} 清除 ${md}`);
    }
  });
  console.log(`${C.g}✓ 卸载完成${C.n}`);
}

// ---------- 入口 ----------
const arg = process.argv[2];
try {
  if (arg === '--uninstall') uninstall();
  else install(arg);
} catch (e) {
  console.error(`${C.r}安装出错：${e.message}${C.n}`);
  console.error('可以把这段报错发给你的 AI 助手，让它帮你修。');
  process.exit(1);
}
