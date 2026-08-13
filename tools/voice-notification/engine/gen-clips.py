# -*- coding: utf-8 -*-
"""生成多标签播报语音 clip（"对话N，搞定啦" / "对话N，需要授权一下"）。

默认只带 1~6 号对话的成品。开更多标签就跑这个脚本补，别手工拿 ffmpeg 默认参数
转 —— 默认参数会踩下面「编码铁律」那两个坑，声音会被掐头去尾。

用法
----
    python gen-clips.py                      # 1~6 号，晓晓音色，输出到本机安装目录
    python gen-clips.py --tabs 10            # 补到 10 号
    python gen-clips.py --voice yunxi        # 换音色（xiaoxiao/xiaoyi/yunxi/yunyang）
    python gen-clips.py --out D:/some/dir    # 指定输出目录
    python gen-clips.py --pad-only D:/dir    # 只给已有 mp3 焊静音+重编码，不重新 TTS

不带 --out 时按这个顺序挑输出目录：
    1) ~/.claude/voice_clips/claudian_multitab/       = AI 装的（推荐那条路）
    2) ~/.task-voice/voice_clips/claudian_multitab/   = install.py 装的
    3) 工具包自己的 voice_clips/claudian_multitab/    = 两处都没装，当成在给分发包补料
前两条是「装给本机用」，第 3 条是「给分发包补料」。跑完看一眼打印的输出路径，
别在没装的机器上跑完就以为生效了。

依赖
----
    pip install edge-tts imageio-ffmpeg
（imageio-ffmpeg 自带 ffmpeg 二进制，不用装系统级 ffmpeg、不用配 PATH）

编码铁律（2026-07-31 实测踩出来的，改参数前先读完）
--------------------------------------------------
Windows 版播放走 MCI（winmm.dll），它算音频长度用的是「文件大小 ÷ 首帧码率」，
而不是真去解码。`play ... wait` 又依赖这个长度决定什么时候返回、然后 close。
所以长度一算错，close 就提前 → 尾巴被掐掉。两个必须踩对的点：

1. 锁 CBR：`-b:a 48k`，绝对不能用 `-q:a`（出 VBR）。
   VBR 下「大小÷首帧码率」的公式直接失效，实测真实 2.64s、MCI 报 1.27s。

2. 禁 Xing 头帧：`-write_xing 0`。← 这条最隐蔽
   48kbps/24000Hz 的 MPEG-2 帧只有 144 字节，装不下 Xing 的 100 字节 TOC，
   ffmpeg 会把这个头帧单独提到 64kbps（192 字节）才塞得进去。MCI 只读首帧码率，
   读到 64 就按 8000 B/s 算整个文件 → 长度一律少报 25%（比值精准 0.75）。
   对照首帧字节：edge-tts 原生 `FF F3 64 C4`（index 6 = 48kbps，对）
                 ffmpeg 默认 `FF F3 84 C0`（index 8 = 64kbps，错）

另外焊 350ms 前置静音（`adelay`）：声卡省电态要 300~500ms 才转起来，open 完立刻
play 的话开头这段就丢了，"对话三搞定啦"会被啃成"话三搞定啦"。前面垫静音后，被啃
掉的是静音、人声一个字不丢。脚本侧的 cue 预热只能缓解，焊进文件才跨机器稳。

验收：MCI 报的长度应 ≈ 文件大小 ÷ 6000 ÷ 1000 秒，差 <50ms。差成 0.75 倍 = Xing 又回来了。
"""
import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi": "zh-CN-XiaoyiNeural",
    "yunxi": "zh-CN-YunxiNeural",
    "yunyang": "zh-CN-YunyangNeural",
}

# 中文数字：播"对话三"比"对话3"自然
CN_NUM = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

PAD_MS = 350
BITRATE = "48k"
RATE = "24000"

def cn(n: int) -> str:
    """1→一, 12→十二, 20→二十, 25→二十五。够用到 99。"""
    if n <= 10:
        return CN_NUM[n]
    if n < 20:
        return "十" + CN_NUM[n - 10]
    tens, ones = divmod(n, 10)
    return CN_NUM[tens] + "十" + (CN_NUM[ones] if ones else "")


def default_out() -> tuple[Path, str]:
    """挑输出目录：先本机安装位置，都没装才落回工具包自己的 voice_clips。

    坑：早期版本直接写死 `engine/../voice_clips/`，那是**微盘共享的工具包目录**。
    用户照文档跑一次，音频进了大家共用的分发包（污染别人），自己 ~/.claude/ 反而
    没变、以为没生效。所以这里必须先认本机安装位置。
    """
    home = Path.home()
    for base, tag in (
        (home / ".claude", "本机安装目录（AI 装的）"),
        (home / ".task-voice", "本机安装目录（install.py 装的）"),
    ):
        if (base / "voice_clips").is_dir():
            return base / "voice_clips" / "claudian_multitab", tag
    pkg = Path(__file__).resolve().parent.parent / "voice_clips" / "claudian_multitab"
    return pkg, "工具包目录（本机没装，当成给分发包补料）"


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
    except ImportError:
        sys.exit("缺 imageio-ffmpeg，先跑：pip install imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def encode(src: Path, dst: Path, ffmpeg: str) -> bool:
    """焊 350ms 前置静音 + 重编码成 MCI 算得准的格式。参数见文件头「编码铁律」。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp.mp3")
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", str(src),
        "-af", f"adelay={PAD_MS}:all=1",
        "-c:a", "libmp3lame",
        "-b:a", BITRATE, "-ar", RATE, "-ac", "1",
        "-map_metadata", "-1",   # 不留元数据
        "-id3v2_version", "0",   # 不写 ID3v2 头，跟 edge-tts 原生一致（裸帧起头）
        "-write_xing", "0",      # ★ 不写 Xing 头帧，否则 MCI 少报 25% 长度、尾巴被掐
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not tmp.exists():
        print(f"  FAIL {dst.name}: {r.stderr.strip()[:150]}")
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(dst)
    return True


def check(p: Path) -> str:
    """自检首帧码率位。48kbps 才对，64kbps 说明 Xing 头帧混进来了。"""
    with open(p, "rb") as f:
        head = f.read(4)
    if head[:3] == b"ID3":
        return "WARN: 带 ID3 头"
    if len(head) < 3 or head[0] != 0xFF:
        return "WARN: 首帧异常"
    idx = head[2] >> 4
    # MPEG-2 Layer III 码率表
    table = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
    kbps = table[idx]
    return "OK 48kbps" if kbps == 48 else f"WARN: 首帧 {kbps}kbps（应为 48）"


async def tts(text: str, voice: str, dst: Path) -> None:
    try:
        import edge_tts
    except ImportError:
        sys.exit("缺 edge-tts，先跑：pip install edge-tts")
    await edge_tts.Communicate(text, voice).save(str(dst))


async def main() -> None:
    ap = argparse.ArgumentParser(description="生成多标签播报语音 clip")
    ap.add_argument("--tabs", type=int, default=6, help="生成到第几号对话（默认 6）")
    ap.add_argument("--voice", default="xiaoxiao", choices=sorted(VOICES), help="音色")
    ap.add_argument("--out", help="输出目录（默认自动挑本机安装目录，见文件头说明）")
    ap.add_argument("--pad-only", metavar="DIR",
                    help="只给该目录下已有 mp3 焊静音+重编码，不重新 TTS")
    ap.add_argument("--start", type=int, default=1, help="从第几号开始（补号用）")
    args = ap.parse_args()

    ffmpeg = ffmpeg_exe()

    # 只重编码模式：拿来救已有的、被默认参数编坏的 clip
    if args.pad_only:
        d = Path(args.pad_only)
        if not d.is_dir():
            sys.exit(f"目录不存在：{d}")
        files = sorted(d.rglob("*.mp3"))
        print(f"重编码 {len(files)} 个文件（{d}）")
        print("⚠️ 只对「没焊过静音」的原始档跑，重复跑会叠加静音、开头越来越长\n")
        ok = 0
        for f in files:
            if encode(f, f, ffmpeg):
                ok += 1
        print(f"\n完成 {ok}/{len(files)}")
        return

    if args.out:
        out, where = Path(args.out), "手动指定"
    else:
        out, where = default_out()
    voice_id = VOICES[args.voice]
    raw = out / "_raw"
    raw.mkdir(parents=True, exist_ok=True)

    jobs = []
    for n in range(args.start, args.tabs + 1):
        jobs.append((f"dialog{n}_done.mp3", f"对话{cn(n)}，搞定啦"))
        jobs.append((f"dialog{n}_perm.mp3", f"对话{cn(n)}，需要授权一下"))

    print(f"音色：{args.voice} ({voice_id})")
    print(f"输出：{out}")
    print(f"　　　（{where}）")
    print(f"编码：CBR {BITRATE} / {RATE}Hz / mono / 无 ID3 / 无 Xing / 前置静音 {PAD_MS}ms\n")

    ok = 0
    for fname, text in jobs:
        tmp_raw = raw / fname
        try:
            await tts(text, voice_id, tmp_raw)
        except Exception as e:
            print(f"  FAIL {fname}: TTS 出错 {e}")
            continue
        if encode(tmp_raw, out / fname, ffmpeg):
            ok += 1
            print(f"  {fname:22} {text:16} {check(out / fname)}")
        tmp_raw.unlink(missing_ok=True)

    # 清掉中转目录，别在成品目录里留垃圾
    try:
        raw.rmdir()
    except OSError:
        pass

    print(f"\n完成 {ok}/{len(jobs)}")
    if ok:
        print("自检全 OK 48kbps 才算对；出现 64kbps = -write_xing 0 被改掉了，回头看文件头说明。")


if __name__ == "__main__":
    # Windows 控制台默认 GBK，中文输出会炸；跑之前设 PYTHONUTF8=1 或用下面这行兜底
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    asyncio.run(main())
