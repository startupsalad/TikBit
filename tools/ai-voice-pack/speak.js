#!/usr/bin/env node
/* ============================================================================
 * TikBit AI 工作台 · 语音朗读引擎 speak.js
 * ----------------------------------------------------------------------------
 * 作用：每次 Claude 回复完，Stop 钩子调用本脚本，把回复念出来。
 * 跨平台：Mac 用系统自带 say，Windows 用系统自带 PowerShell 语音。
 * 零额外依赖：只用 Node 内置模块（Node 是 Claude Code 的硬依赖，一定有）。
 * 0 费用 0 token 离线可用。
 *
 * 工作流程：
 *   1) 从 stdin 读 Stop 钩子传入的 JSON（含 transcript_path）
 *   2) 读开关文件，关了就直接退出（静音）
 *   3) 解析 transcript，取出 Claude 最后一条回复的纯文字
 *   4) 优先取 <!--SPEAK: ...--> 标记里的口语简化版；没有就自动简化第一段
 *   5) 调系统语音念出来（后台异步，不阻塞 Claude）
 *
 * 出任何错都安静退出（exit 0），绝不打断用户正常使用 Claude。
 * ========================================================================== */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

// ---------- 路径常量 ----------
const HOME = os.homedir();
const PKG_DIR = path.join(HOME, '.claude', 'ss-speak');   // 本包安装目录
const FLAG_ON = path.join(PKG_DIR, 'ON');                  // 开关文件：存在=开，不存在=关
const CONFIG = path.join(PKG_DIR, 'config.json');          // 声音/语速等配置
const LOG = path.join(PKG_DIR, 'last-run.log');            // 排错日志（只留最近一次）
const LAST_SPOKEN = path.join(PKG_DIR, '.last-spoken');    // 上次念过的内容（去重，防重念旧总结）

// ---------- 小工具：写排错日志（出错也能让用户的 Claude 看懂）----------
function log(msg) {
  try {
    const line = `[${new Date().toISOString()}] ${msg}\n`;
    fs.appendFileSync(LOG, line);
  } catch (_) { /* 日志失败也不能影响主流程 */ }
}

// ---------- 安静退出（任何异常都走这里）----------
function quietExit(reason) {
  if (reason) log('SKIP: ' + reason);
  process.exit(0);
}

// ---------- 读配置（带默认值）----------
function loadConfig() {
  const def = {
    macVoice: 'Lilian',    // 想用的声音。Lilian(Premium·黎潋)音质好，没装会自动降级到婷婷
    winVoice: '',          // 留空=用系统默认中文声；可填 Huihui 等
    rate: '150',           // Mac: 每分钟字数；Win: -10~10。150≈2.5字/秒，不赶、停顿更自然
    maxChars: 150,         // 念出来的最大字数。Lilian约2.5字/秒，150字≈60秒，超了截断
    sound: 'hero'          // 朗读前的完成音效：hero(通关音)/glass/ping/pop/none
  };
  try {
    const c = JSON.parse(fs.readFileSync(CONFIG, 'utf8'));
    return Object.assign(def, c);
  } catch (_) {
    return def;
  }
}

// ---------- 把 Markdown/富文本清成适合朗读的纯人话 ----------
function cleanForSpeech(text) {
  let t = text;
  // 去掉 SPEAK 标记本身（万一混进来）
  t = t.replace(/<!--\s*SPEAK:?/gi, '').replace(/-->/g, '');
  // 去掉代码块（```...```）整段
  t = t.replace(/```[\s\S]*?```/g, ' ');
  // 去掉行内代码 `xxx`
  t = t.replace(/`[^`]*`/g, ' ');
  // 图片 ![alt](url) / ![[xx]] → 去掉
  t = t.replace(/!\[\[[^\]]*\]\]/g, ' ').replace(/!\[[^\]]*\]\([^)]*\)/g, ' ');
  // 链接 [text](url) → 只留 text
  t = t.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1');
  // Wiki 链接 [[path/name|alias]] / [[path/name]] → 只留最后一段名字
  t = t.replace(/\[\[([^\]]*)\]\]/g, (m, p1) => {
    const seg = p1.split('|').pop().split('/').pop();
    return seg.replace(/\.md$/i, '');
  });
  // 标题井号、引用号、列表符号
  t = t.replace(/^#{1,6}\s*/gm, '').replace(/^>\s?/gm, '').replace(/^[\-\*\+]\s+/gm, '');
  // 加粗/斜体 ** * __ _
  t = t.replace(/\*\*([^*]*)\*\*/g, '$1').replace(/\*([^*]*)\*/g, '$1');
  t = t.replace(/__([^_]*)__/g, '$1').replace(/_([^_]*)_/g, '$1');
  // 表格分隔、水平线
  t = t.replace(/^\s*\|.*\|\s*$/gm, ' ').replace(/^[\-\=]{3,}\s*$/gm, ' ');
  // 去掉大部分 emoji 和杂符号（保留中英文、数字、常用中文标点）
  t = t.replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2190}-\u{21FF}\u{2B00}-\u{2BFF}️]/gu, ' ');
  // 多余空白合并
  t = t.replace(/\s+/g, ' ').trim();
  return t;
}

// ---------- 从 transcript 取出 Claude 最后一条回复的文字 ----------
function getLastAssistantText(transcriptPath) {
  const raw = fs.readFileSync(transcriptPath, 'utf8');
  const lines = raw.split('\n').filter(Boolean);
  // 从后往前找最后一条 assistant 且含 text 块的消息
  for (let i = lines.length - 1; i >= 0; i--) {
    let obj;
    try { obj = JSON.parse(lines[i]); } catch (_) { continue; }
    if (obj.type !== 'assistant' || !obj.message) continue;
    const content = obj.message.content;
    if (!Array.isArray(content)) continue;
    const texts = content.filter(b => b && b.type === 'text' && b.text).map(b => b.text);
    if (texts.length) return texts.join('\n');
  }
  return '';
}

// ---------- 智能截断：软上限 + 说完整句子 ----------
// 理念：目的是"别太长"，不是"卡死 60 秒"。所以 maxChars 是软目标，不是硬刀。
//   ① 没到软目标 → 全念；
//   ② 到了软目标 → 把"当前这句话说完"再停（宁可略超，也要说完整，听感自然）；
//   ③ 硬天花板(≈软目标×1.5)只是安全网，防止极端流水句无限长，正常碰不到。
function smartTruncate(s, softTarget, hardCeiling) {
  if (!s) return s;
  if (s.length <= softTarget) return s; // 没超软目标，原样全念
  // 按句子切（保留句末标点），累加到刚好够软目标，在完整句子处收尾
  const parts = s.match(/[^。！？!?]*[。！？!?]+|[^。！？!?]+$/g) || [s];
  let acc = '';
  for (const seg of parts) {
    acc += seg;
    if (acc.length >= softTarget) break; // 够长了，且停在一句话结束处
  }
  acc = acc.trim();
  // 安全网：万一是没标点的超长流水句，别让它突破硬天花板
  if (acc.length > hardCeiling) {
    const cut = acc.slice(0, hardCeiling);
    const commaLp = Math.max(cut.lastIndexOf('，'), cut.lastIndexOf('、'), cut.lastIndexOf(','));
    acc = commaLp > hardCeiling * 0.5 ? cut.slice(0, commaLp) : cut;
  }
  return acc;
}

// ---------- 决定到底念什么 ----------
function pickSpeech(fullText, cfg) {
  const softTarget = cfg.maxChars;
  const hardCeiling = cfg.maxCharsHard || Math.round(cfg.maxChars * 1.5);
  // 1) 优先：<!--SPEAK: 这里是口语简化版 -->（AI 主动写的总结，最理想）
  const m = fullText.match(/<!--\s*SPEAK:?([\s\S]*?)-->/i);
  if (m && m[1].trim()) {
    let s = cleanForSpeech(m[1]);
    // 软上限：没超就全念，超了把当前句子说完再停（宁可略超，不卡半句）
    s = smartTruncate(s, softTarget, hardCeiling);
    return s;
  }
  // 2) 保底：没有标记 → 不念整段原文（那样又长又不像总结），
  //    只念「第一句」。因为回复第一句几乎都是结论/总结，念出来最像人话。
  let cleaned = cleanForSpeech(fullText);
  if (!cleaned) return '';
  // 按中英文句末标点切第一句
  const mm = cleaned.match(/^[\s\S]*?[。！？!?](?=\s|$|[^.0-9])/);
  let first = mm ? mm[0].trim() : cleaned;
  // 第一句太短（像「好的。」），补上第二句，信息更完整
  if (first.length < 12) {
    const rest = cleaned.slice(first.length);
    const mm2 = rest.match(/^[\s\S]*?[。！？!?](?=\s|$|[^.0-9])/);
    if (mm2) first = (first + mm2[0]).trim();
  }
  // 仍然超长就用软上限收尾（说完整句子，别停在逗号上）
  first = smartTruncate(first, softTarget, hardCeiling);
  return first;
}

// ---------- 播放完成音效（朗读前的「叮」，给孩子游戏通关感）----------
// Mac: 用系统自带音效文件 + afplay；Win: 用 PowerShell beep 拼一个上扬通关音。
// 全部零依赖、老系统也有。返回大致时长(ms)，好让语音稍微错开音效。
function playSound(name, plat) {
  if (!name || name === 'none') return 0;
  if (plat === 'darwin') {
    const map = {
      hero: 'Hero.aiff', glass: 'Glass.aiff', ping: 'Ping.aiff', pop: 'Pop.aiff'
    };
    const file = '/System/Library/Sounds/' + (map[name] || 'Hero.aiff');
    try {
      if (!fs.existsSync(file)) return 0;
      const c = spawn('afplay', [file], { detached: true, stdio: 'ignore' });
      c.on('error', () => {});
      c.unref();
      log('SOUND(mac): ' + name);
      return 700; // Hero 约 0.7s，语音稍微等一下更自然
    } catch (_) { return 0; }
  }
  if (plat === 'win32') {
    // Windows 没有 Hero.aiff，用 Console.Beep 拼一个上扬的「通关」音序
    const seq = {
      hero: '[console]::beep(784,90);[console]::beep(988,90);[console]::beep(1319,160)',
      glass: '[console]::beep(1319,120)',
      ping: '[console]::beep(988,120)',
      pop: '[console]::beep(660,80)'
    };
    const ps = seq[name] || seq.hero;
    try {
      const c = spawn('powershell', ['-NoProfile', '-Command', ps],
        { detached: true, stdio: 'ignore', windowsHide: true });
      c.on('error', () => {});
      c.unref();
      log('SOUND(win): ' + name);
      return 450;
    } catch (_) { return 0; }
  }
  return 0;
}

// ---------- Mac 声音智能回退 ----------
// 配置想用的声音（如 Lilian Premium）系统可能没装。检测一下：装了就用，
// 没装就降级到标准中文声（婷婷一定有），再不行交给系统默认。
// 这样：下载了高音质声音的人自动享受好音质，没下载的人也有声音不报错。
let _voiceCache = null;
function installedVoices() {
  if (_voiceCache) return _voiceCache;
  try {
    const out = require('child_process').execSync('say -v "?"', { encoding: 'utf8', timeout: 2000 });
    // 每行形如：Lilian (Premium)    zh_CN    # 你好
    _voiceCache = out.split('\n').map(line => {
      const name = line.split(/\s{2,}/)[0].trim();          // 「Lilian (Premium)」
      const base = name.split(' (')[0].trim();              // 「Lilian」
      return { name, base };
    }).filter(v => v.base);
  } catch (_) { _voiceCache = []; }
  return _voiceCache;
}
function resolveMacVoice(preferred) {
  const list = installedVoices();
  if (!list.length) return preferred || ''; // 查不到就按原样交给 say
  const has = base => list.some(v => v.base.toLowerCase() === String(base).toLowerCase());
  // 1) 配置指定的声音装了就用
  if (preferred && has(preferred)) return preferred;
  // 2) 降级链：优先标准普通话女声婷婷（紧凑版一定有）
  for (const fb of ['Tingting', 'Sinji', 'Meijia']) {
    if (has(fb)) { log('voice fallback: ' + preferred + ' -> ' + fb); return fb; }
  }
  // 3) 都没有，交给系统默认（args 不带 -v）
  log('voice fallback: ' + preferred + ' -> system default');
  return '';
}

// ---------- 调系统语音（后台异步，不阻塞）----------
function speak(text, cfg) {
  const plat = process.platform;
  // 先播完成音效（游戏通关感），拿到大致时长好让语音稍微错开
  const soundMs = playSound(cfg.sound, plat);

  if (plat === 'darwin') {
    // Mac: say。先杀掉正在念的，避免叠音
    try { spawn('killall', ['say'], { stdio: 'ignore' }).on('error', () => {}); } catch (_) {}
    const args = [];
    const useVoice = resolveMacVoice(cfg.macVoice);
    if (useVoice) args.push('-v', useVoice);
    if (cfg.rate) args.push('-r', String(cfg.rate));
    // ⚠️ 不走 stdin 管道：say 是 detached+unref 的后台进程，node 一退出，
    //   OS 管道缓冲区里 say 还没读走的文本就被丢弃 → 长句只念开头几个字就断
    //   （现象："全搞定啦"后戛然而止）。
    // 正解：把文本写进临时文件，让 say -f 自己独立读完整篇，node 退出也不影响。
    const SAY_FILE = path.join(PKG_DIR, '.say-text.txt');
    try { fs.writeFileSync(SAY_FILE, text, 'utf8'); }
    catch (e) { return log('say write file failed: ' + e.message); }
    args.push('-f', SAY_FILE);
    const doSay = () => {
      const child = spawn('say', args, { detached: true, stdio: 'ignore' });
      child.on('error', e => log('say error: ' + e.message));
      child.unref();
      log('SPOKEN(mac): ' + text.slice(0, 60));
    };
    // 等音效播一下再开口，避免音效盖住头一个字
    if (soundMs > 0) setTimeout(doSay, soundMs); else doSay();
  } else if (plat === 'win32') {
    // Windows: 用系统自带 System.Speech（Vista+ 都有，老系统也行）
    const rate = cfg.rate ? `$s.Rate=${parseInt(cfg.rate, 10) || 0};` : '';
    const voice = cfg.winVoice ? `try{$s.SelectVoice('${cfg.winVoice.replace(/'/g, "''")}')}catch{};` : '';
    // 文本经 base64 传入，彻底避开引号/换行/编码地雷
    const b64 = Buffer.from(text, 'utf16le').toString('base64');
    // Win 把「短暂等待 + 朗读」放进同一个 PowerShell，避免再起进程
    const wait = soundMs > 0 ? `Start-Sleep -Milliseconds ${soundMs};` : '';
    const ps = [
      wait,
      'Add-Type -AssemblyName System.Speech;',
      '$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;',
      voice, rate,
      `$t=[System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('${b64}'));`,
      '$s.Speak($t);'
    ].join('');
    const child = spawn('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps],
      { detached: true, stdio: 'ignore', windowsHide: true });
    child.on('error', e => log('powershell error: ' + e.message));
    child.unref();
    log('SPOKEN(win): ' + text.slice(0, 60));
  } else {
    quietExit('unsupported platform: ' + plat);
  }
}

// ---------- 主流程 ----------
function main() {
  // 开关：没开就静音退出
  if (!fs.existsSync(FLAG_ON)) quietExit('switch off');

  // 读 stdin（Stop 钩子的 JSON）
  let input = '';
  process.stdin.setEncoding('utf8');
  // stdin 兜底超时（钩子没喂数据时别卡住）
  const stdinTimer = setTimeout(() => quietExit('stdin timeout'), 3000);
  process.stdin.on('data', d => { input += d; });
  process.stdin.on('end', () => {
    clearTimeout(stdinTimer);
    let transcriptPath = '';
    try {
      const payload = JSON.parse(input || '{}');
      transcriptPath = payload.transcript_path || '';
    } catch (e) { return quietExit('bad stdin json'); }

    if (!transcriptPath || !fs.existsSync(transcriptPath)) {
      return quietExit('no transcript: ' + transcriptPath);
    }

    const cfg = loadConfig();

    // 取最后一条回复文字。⚠️ 竞速：Stop 钩子可能抢在"最终总结落盘"之前触发，
    // 读到的会是更早的上一段文字（比如工具调用前的一句小标题）。
    // 对策：若读到的文字里没有 SPEAK 标记，很可能总结还在落盘途中 →
    //   稍等重读，最多 RETRY_MAX 次；读到带标记的就用。
    //   实在等不到（这条回复确实没写标记）才用兜底（念第一句）。
    const RETRY_MAX = 6;       // 最多重试次数
    const RETRY_DELAY = 350;   // 每次间隔(ms)，6×350≈2.1s 足够落盘
    let attempt = 0;

    const tryRead = () => {
      let full = '';
      try { full = getLastAssistantText(transcriptPath); }
      catch (e) { return quietExit('read transcript failed: ' + e.message); }

      const hasSpeak = /<!--\s*SPEAK/i.test(full);
      // 没读到 SPEAK 标记 且 还有重试机会 → 等一下再读（赌总结正在落盘）
      if (!hasSpeak && attempt < RETRY_MAX) {
        attempt++;
        log('no SPEAK yet, retry ' + attempt + '/' + RETRY_MAX);
        return setTimeout(tryRead, RETRY_DELAY);
      }
      if (!full.trim()) return quietExit('empty assistant text');

      const toSpeak = pickSpeech(full, cfg);
      if (!toSpeak.trim()) return quietExit('nothing to speak after clean');

      // ⚠️ 去重：防止"重念旧总结"。继续/重开对话时，钩子读到的"最后一条回复"
      //   可能是几小时前那条旧总结（它也带 SPEAK 标记），重试逻辑会误念出来 →
      //   你听到的语音和眼前的新文字对不上。对策：和上次念的完全一样就跳过。
      let lastSpoken = '';
      try { lastSpoken = fs.readFileSync(LAST_SPOKEN, 'utf8'); } catch (_) {}
      if (toSpeak.trim() === lastSpoken.trim()) {
        return quietExit('same as last spoken, skip (避免重念旧总结)');
      }
      try { fs.writeFileSync(LAST_SPOKEN, toSpeak); } catch (_) {}

      try { speak(toSpeak, cfg); }
      catch (e) { return quietExit('speak failed: ' + e.message); }
      // 不调 process.exit：让事件循环自然结束。
      // Mac 的语音可能用 setTimeout 延后触发（等音效），子进程都 detached+unref，
      // 触发后 spawn 完进程就自然退出，语音/音效在后台继续播。
    };
    tryRead();
  });
}

try { main(); } catch (e) { quietExit('fatal: ' + e.message); }
