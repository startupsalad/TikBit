#!/usr/bin/env node
/* ============================================================================
 * TikBit AI 工作台 · 语音朗读包 · 核心安装器 install-core.js
 * ----------------------------------------------------------------------------
 * 跨平台一份逻辑，Mac 的 .command 和 Windows 的 .bat 都调它。
 * 干的活：
 *   1) 建目录 ~/.claude/ss-speak/
 *   2) 拷 speak.js 进去
 *   3) 写默认 config.json（不覆盖用户已有的）
 *   4) 建开关文件 ON（默认开启）
 *   5) 合并（不覆盖）~/.claude/settings.json 的 Stop 钩子
 *   6) 往 ~/.claude/CLAUDE.md 追加「语音行为指令」（让 Claude 会写 SPEAK 标记 + 响应开关口令）
 *
 * 用法：node install-core.js <speak.js的绝对路径>
 * 卸载：node install-core.js --uninstall
 * ========================================================================== */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const CLAUDE_DIR = path.join(HOME, '.claude');
const PKG_DIR = path.join(CLAUDE_DIR, 'ss-speak');
const SETTINGS = path.join(CLAUDE_DIR, 'settings.json');
const CLAUDE_MD = path.join(CLAUDE_DIR, 'CLAUDE.md');
const FLAG_ON = path.join(PKG_DIR, 'ON');
const CONFIG = path.join(PKG_DIR, 'config.json');
const SPEAK_DEST = path.join(PKG_DIR, 'speak.js');

// 钩子命令：用当前 node 跑 speak.js（绝对路径，绕开 PATH 问题）
const HOOK_CMD_MARK = 'ss-speak/speak.js'; // 用来识别「是不是我们的钩子」

const C = { g: '\x1b[1;32m', y: '\x1b[1;33m', r: '\x1b[1;31m', b: '\x1b[1;36m', n: '\x1b[0m' };
const ok = m => console.log(`${C.g}  ✓${C.n} ${m}`);
const info = m => console.log(`${C.b}  ·${C.n} ${m}`);
const warn = m => console.log(`${C.y}  !${C.n} ${m}`);

// ---------- 读 JSON（容错）----------
function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (_) { return null; }
}

// ---------- 合并 Stop 钩子（保留用户已有的所有 hooks/设置）----------
function mergeStopHook(nodeExec) {
  let cfg = readJson(SETTINGS) || {};
  if (typeof cfg !== 'object' || Array.isArray(cfg)) cfg = {};
  if (!cfg.hooks || typeof cfg.hooks !== 'object') cfg.hooks = {};
  if (!Array.isArray(cfg.hooks.Stop)) cfg.hooks.Stop = [];

  // 钩子命令：node 路径 + speak.js 路径都用绝对路径
  const command = `"${nodeExec}" "${SPEAK_DEST}"`;

  // 先删掉我们之前装过的（避免重复 / 升级旧命令）
  cfg.hooks.Stop = cfg.hooks.Stop.filter(entry => {
    if (!entry || !Array.isArray(entry.hooks)) return true;
    return !entry.hooks.some(h => h && typeof h.command === 'string' && h.command.includes(HOOK_CMD_MARK));
  });

  // 加我们的（matcher 留空=所有 Stop 都触发）
  cfg.hooks.Stop.push({
    hooks: [{ type: 'command', command }]
  });

  // 备份后写入
  if (fs.existsSync(SETTINGS)) {
    try { fs.copyFileSync(SETTINGS, SETTINGS + '.ss-speak.bak'); } catch (_) {}
  }
  fs.writeFileSync(SETTINGS, JSON.stringify(cfg, null, 2));
}

// ---------- 追加 CLAUDE.md 行为指令（带唯一标记，重复装不会叠加）----------
// 内部标记 ID 保持 SS-SPEAK（勿改，改了老用户旧块删不掉、会残留重复）
const MD_ID = 'SS-SPEAK';
const MD_BEGIN = `<!-- ${MD_ID}-BEGIN TikBit语音朗读包·勿删此标记 -->`;
const MD_END = `<!-- ${MD_ID}-END -->`;
// 清理用正则：只锚定品牌无关的 ID 标记，所以老用户 CLAUDE.md 里带旧品牌名的块也能被认出来、正常替换/删除
const mdRe = () => new RegExp('<!--\\s*' + MD_ID + '-BEGIN[\\s\\S]*?' + MD_ID + '-END\\s*-->', 'g');
const MD_BLOCK = `${MD_BEGIN}
## 🔊 语音朗读（TikBit AI 工作台）

我（Claude）安装了语音朗读功能，每次回复完会把内容念出来给小朋友听。请遵守：

1. **每次回复的最后，附一段「这一轮做了什么」的口语总结**，用这个格式（用户看不到这段、但会被念出来）：
   \`<!--SPEAK: 这里写口语化的总结-->\`
   - **内容配方（核心：写"用户需要知道的"，不是"我干了啥"）**：按 ①结论 → ②关键变化/发现 → ③下一步 的顺序，能省则省。
     - ① **结论**（永远先说）：这事成没成、结果是什么。
     - ② **关键变化/发现**（有才说）：有什么你该知道的改动或新情况。
     - ③ **下一步**（有才说）：要不要用户做什么，或我接着干啥。
     - 一句话：**先说结果，再说影响，最后说行动**。站在用户视角（这事对你意味着什么），不是我的工作视角（改了哪几个文件）。
     - ❌反例：「我修改了脚本，新增了函数，替换了两处逻辑。」 ✅正例：「语音卡半句的毛病修好啦，以后会把话说完整再停，你新开对话就能听到。」
   - **长度（软上限，不是硬刀）**：目标 **120-150 字以内**（约 60 秒）。目的是"别太长"，不是"卡死 60 秒"——**宁可略超也要把句子说完整，结尾落在句号**。能说清就尽量短，别凑字。脚本端已有软上限+硬天花板兜底，但最好一开始就写在目标内、自带句号收尾，根本不触发截断。
   - **语气**：像一起闯关的小伙伴——活泼、清楚、正能量，但**信息要实在**。
   - **不要**念代码、路径、长串符号、文件名。
   - 例：\`<!--SPEAK: 搞定啦！语音卡半句的毛病修好了，现在会把话说完整再停，不会突然断掉。你新开个对话就能听到效果咯！-->\`
2. **语音开关口令**（用户说这些话时，照做并回一句确认）：
   - 「开启语音 / 打开语音 / 我要听声音」→ 创建文件 \`~/.claude/ss-speak/ON\`（\`touch\` 或写空文件）
   - 「关闭语音 / 静音 / 别出声了」→ 删除文件 \`~/.claude/ss-speak/ON\`
   - 「换个声音 / 语速快点慢点 / 关掉音效 / 总结长一点短一点」→ 改 \`~/.claude/ss-speak/config.json\`（字段：macVoice/winVoice/rate/sound/maxChars）
3. 这是给孩子用的，全程保持**鼓励、有趣、安全**。
${MD_END}`;

function appendClaudeMd(targetPath) {
  let cur = '';
  try { cur = fs.readFileSync(targetPath, 'utf8'); } catch (_) { cur = ''; }
  // 去掉旧的同标记块（升级时替换；含旧品牌名的块也会被清掉）
  const re = mdRe();
  cur = cur.replace(re, '').replace(/\n{3,}/g, '\n\n').trim();
  const next = (cur ? cur + '\n\n' : '') + MD_BLOCK + '\n';
  fs.writeFileSync(targetPath, next);
}

// ---------- 从 obsidian.json 找到「当前打开的知识库」CLAUDE.md 路径 ----------
// Claude Code 在 Obsidian 里跑时，加载的是知识库自己的 CLAUDE.md（不是全局那个），
// 所以「每次写 SPEAK 总结」的指令必须也写进知识库 CLAUDE.md，否则 AI 收不到提醒。
function findVaultClaudeMds() {
  const candidates = [];
  // obsidian.json 各平台位置
  const obsPaths = process.platform === 'win32'
    ? [path.join(process.env.APPDATA || path.join(HOME, 'AppData/Roaming'), 'obsidian', 'obsidian.json')]
    : [path.join(HOME, 'Library/Application Support/obsidian/obsidian.json'),
       path.join(HOME, '.config/obsidian/obsidian.json')];
  for (const op of obsPaths) {
    const j = readJson(op);
    if (!j || !j.vaults) continue;
    for (const v of Object.values(j.vaults)) {
      if (v && v.path) candidates.push(path.join(v.path, 'CLAUDE.md'));
    }
  }
  return candidates;
}

// ---------- 卸载 ----------
function uninstall() {
  // 1) settings.json 摘掉钩子
  const cfg = readJson(SETTINGS);
  if (cfg && cfg.hooks && Array.isArray(cfg.hooks.Stop)) {
    cfg.hooks.Stop = cfg.hooks.Stop.filter(entry => {
      if (!entry || !Array.isArray(entry.hooks)) return true;
      return !entry.hooks.some(h => h && typeof h.command === 'string' && h.command.includes(HOOK_CMD_MARK));
    });
    if (cfg.hooks.Stop.length === 0) delete cfg.hooks.Stop;
    if (cfg.hooks && Object.keys(cfg.hooks).length === 0) delete cfg.hooks;
    fs.writeFileSync(SETTINGS, JSON.stringify(cfg, null, 2));
    ok('已从 settings.json 移除语音钩子');
  }
  // 2) CLAUDE.md 去掉指令块（全局 + 各知识库）
  const stripMd = (file) => {
    try {
      let cur = fs.readFileSync(file, 'utf8');
      const re = mdRe();
      if (!re.test(cur)) return false;
      cur = cur.replace(re, '').replace(/\n{3,}/g, '\n\n').trim() + '\n';
      fs.writeFileSync(file, cur);
      return true;
    } catch (_) { return false; }
  };
  let mdCount = 0;
  if (stripMd(CLAUDE_MD)) mdCount++;
  for (const md of findVaultClaudeMds()) { if (stripMd(md)) mdCount++; }
  if (mdCount) ok(`已从 ${mdCount} 个 CLAUDE.md 移除语音指令`);
  // 3) 删包目录（保留日志方便排错？这里直接删干净）
  try { fs.rmSync(PKG_DIR, { recursive: true, force: true }); ok('已删除 ~/.claude/ss-speak/'); } catch (_) {}
  console.log(`\n${C.g}语音朗读包已卸载。${C.n}\n`);
}

// ---------- 安装 ----------
function install(speakSrc) {
  if (!speakSrc || !fs.existsSync(speakSrc)) {
    console.error(`${C.r}找不到 speak.js：${speakSrc}${C.n}`);
    process.exit(1);
  }
  fs.mkdirSync(PKG_DIR, { recursive: true });
  ok('创建目录 ~/.claude/ss-speak/');

  fs.copyFileSync(speakSrc, SPEAK_DEST);
  ok('安装朗读引擎 speak.js');

  // 默认配置（已存在则不覆盖，保住用户自定义）
  if (!fs.existsSync(CONFIG)) {
    const def = { macVoice: 'Lilian', winVoice: '', rate: '150', maxChars: 150, maxCharsHard: 225, sound: 'hero' };
    fs.writeFileSync(CONFIG, JSON.stringify(def, null, 2));
    ok('写入默认配置（黎潋 Lilian 高音质普通话 + Hero 通关音效）');
  } else {
    info('已有 config.json，保留你的自定义设置');
  }

  // 默认开启
  if (!fs.existsSync(FLAG_ON)) { fs.writeFileSync(FLAG_ON, ''); }
  ok('语音已默认开启（开关文件 ON）');

  // 合并钩子
  const nodeExec = process.execPath; // 当前 node 的绝对路径
  mergeStopHook(nodeExec);
  ok('已登记 Stop 钩子到 settings.json（保留你原有设置）');

  // CLAUDE.md 指令：① 全局兜底 ② 各知识库（关键——Obsidian 里加载的是知识库的 CLAUDE.md）
  appendClaudeMd(CLAUDE_MD);
  ok('已写入语音行为指令到 ~/.claude/CLAUDE.md（全局兜底）');
  const vaultMds = findVaultClaudeMds();
  if (vaultMds.length) {
    let n = 0;
    for (const md of vaultMds) {
      try {
        // 知识库文件夹一定存在（obsidian 登记过），CLAUDE.md 没有就新建
        if (fs.existsSync(path.dirname(md))) { appendClaudeMd(md); n++; }
      } catch (_) {}
    }
    if (n) ok(`已写入语音行为指令到 ${n} 个 Obsidian 知识库的 CLAUDE.md（让 AI 每次都做口语总结）`);
  } else {
    info('没找到 Obsidian 知识库；AI 首次回复可能念原文截断，正常用就会读到全局指令');
  }

  console.log(`\n${C.g}========================================${C.n}`);
  console.log(`${C.g}  🔊 语音朗读包安装成功！${C.n}`);
  console.log(`${C.g}========================================${C.n}`);
  console.log(`\n  ${C.b}下一步：${C.n}回到 Obsidian，新开一个对话跟 AI 说句话，`);
  console.log(`  它回复完就会念出来啦（先「叮」一声通关音 + 普通话朗读）。\n`);
  console.log(`  ${C.b}想静音？${C.n}对 AI 说「关闭语音」；想再开就说「开启语音」。\n`);
}

// ---------- 入口 ----------
const arg = process.argv[2];
try {
  if (arg === '--uninstall') uninstall();
  else install(arg);
} catch (e) {
  console.error(`${C.r}安装出错：${e.message}${C.n}`);
  console.error(`可以把这段报错发给你的 AI 助手，让它帮你修。`);
  process.exit(1);
}
