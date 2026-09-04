#!/usr/bin/env node
/* ============================================================================
 * TikBit AI 工作台 · AI 自我成长工具 · 核心安装器 install-core.js
 * ----------------------------------------------------------------------------
 * 跨平台一份逻辑。首选「把整个文件夹交给用户的 AI，让 AI 跑这个脚本」。
 *
 * 和别的工具不同：这个工具不装进系统目录 ~/.claude/，而是装进
 * 用户的 Obsidian 知识库里 —— 因为它是「记忆产品」，要让用户看得见 AI 在长大。
 *
 * 干的活（对每一个 Obsidian 知识库）：
 *   1) 在知识库里建「🌱AI成长档案/」文件夹
 *   2) 把「成长大脑」(机制+方法论)复制进去 —— 覆盖式（这是产品文档，整体刷新）
 *   3) 把「记忆模板」(经验库+项目记忆模板)复制进去 —— ⚠️不覆盖已有（用户的记忆是资产，绝不能抹）
 *   4) 往该知识库的 CLAUDE.md 和 AGENTS.md 各追加一段「自我成长行为指令」（带唯一标记，重复装不叠加）
 *      —— CLAUDE.md 给 Claude 读、AGENTS.md 给 GPT(Codex) 读：一个知识库，两个大脑都会成长。
 *
 * 用法：
 *   node install-core.js <这个文件夹里的「核心」目录>   # 安装
 *   node install-core.js --uninstall                    # 卸载（只去指令，保留成长档案）
 * ========================================================================== */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const IS_WIN = process.platform === 'win32';
const ARCHIVE_NAME = '🌱AI成长档案';   // 装进知识库的文件夹名

const C = { g: '\x1b[1;32m', y: '\x1b[1;33m', r: '\x1b[1;31m', b: '\x1b[1;36m', n: '\x1b[0m' };
const ok = m => console.log(`${C.g}  ✓${C.n} ${m}`);
const info = m => console.log(`${C.b}  ·${C.n} ${m}`);
const warn = m => console.log(`${C.y}  !${C.n} ${m}`);

// ---------- 读 JSON（容错）----------
function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (_) { return null; }
}

// ---------- 递归复制目录（覆盖式，用于成长大脑）----------
function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const ent of fs.readdirSync(src, { withFileTypes: true })) {
    if (ent.name === '.DS_Store' || ent.name === '.WeDrive') continue;
    const s = path.join(src, ent.name);
    const d = path.join(dst, ent.name);
    if (ent.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

// ---------- 复制单文件，但绝不覆盖已存在的（用于记忆文件）----------
function copyFileKeep(src, dst) {
  if (fs.existsSync(dst)) return false;   // 已有就保留，不动用户的记忆
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
  return true;
}

// ---------- 从 obsidian.json 找各知识库目录 ----------
function findVaultDirs() {
  const out = [];
  const obsPaths = IS_WIN
    ? [path.join(process.env.APPDATA || path.join(HOME, 'AppData/Roaming'), 'obsidian', 'obsidian.json')]
    : [path.join(HOME, 'Library/Application Support/obsidian/obsidian.json'),
       path.join(HOME, '.config/obsidian/obsidian.json')];
  for (const op of obsPaths) {
    const j = readJson(op);
    if (!j || !j.vaults) continue;
    for (const v of Object.values(j.vaults)) {
      if (v && v.path && fs.existsSync(v.path)) out.push(v.path);
    }
  }
  return out;
}

// ---------- 行为指令块（写进 CLAUDE.md + AGENTS.md，带唯一标记，重复装不叠加）----------
// 一个知识库两个大脑：CLAUDE.md 给 Claude 读，AGENTS.md 给 GPT(Codex) 读。
// 两份指令内容对称，只是"我是谁"称呼和"更新哪个文件"随大脑不同（并互相同步，保持两个大脑看到同一个你）。
// ★ MD_ID 是品牌无关的内部 ID，永不改。清理正则只锚定它，不锚品牌名，
//   这样带任何历史品牌名的旧块（旧品牌名/新品牌名/未来任何名字）都能被认出来正常替换/删除。
//   反面教材：曾用 esc(MD_BEGIN) 把品牌名整串锚进正则 → 改名后老用户重装叠出重复块、卸载删不掉。
const MD_ID = 'AI-GROWTH';
const MD_BEGIN = `<!-- ${MD_ID}-BEGIN TikBit AI自我成长工具·勿删此标记 -->`;
const MD_END = `<!-- ${MD_ID}-END -->`;
const mdRe = () => new RegExp('<!--\\s*' + MD_ID + '-BEGIN[\\s\\S]*?' + MD_ID + '-END\\s*-->', 'g');

// agent=大脑名(Claude/GPT)；myFile=我读的说明书；twinFile=另一个大脑的说明书
function mdBlock(agent, myFile, twinFile) {
  return `${MD_BEGIN}
## 🌱 AI 自我成长机制（TikBit AI 工作台）

我（${agent}）装了「AI 自我成长工具」——让我越用越懂你。机制文档在本知识库的 \`${ARCHIVE_NAME}/\` 文件夹里（我和另一个大脑共用这一份）。请遵守这套**自动成长**规则：

**核心发动机（最重要）**：每做完一件像样的事、或返工纠错后，我自己过一遍——这一轮有没有值得记下来的？关于**你这个人**、**当前项目**、或**怎么把某类事做好**的经验/坑？有就**主动记下来，记完跟你说一句，不用等你开口**。

我在三个方向慢慢长大：
1. **越来越懂你的人**：在聊天/干活中**顺手留意**你是谁、做什么、说话和做事的偏好——观察到比较确定的特征，就悄悄更新本知识库根目录 \`${myFile}\` 的「我是谁 / 我希望 AI 怎么帮我」，**并把这类两个大脑都该知道的基本信息同步一份到隔壁的 \`${twinFile}\`**（这样你换用另一个大脑时不用重新自我介绍）。只记真实观察到的，不编造；是润物细无声，不是每轮邀功。
2. **越来越懂你的事**：会跨多次对话的项目，给它建 \`[项目名] 项目记忆.md\` 放进项目自己的文件夹（放知识库里，两个大脑都读得到）。你说"继续 XX 项目"时，我**先读它再动手**，无缝接上不让你重新复盘。规范见 \`${ARCHIVE_NAME}/项目记忆规范.md\`，模板见 \`${ARCHIVE_NAME}/项目记忆模板.md\`。
3. **越来越懂怎么做**：踩了坑、返了工、发现好方法后，判断这条经验以后还用得上吗？用得上就写进 \`${ARCHIVE_NAME}/经验与避坑库.md\`（写清 是什么/为什么/怎么用）——这份经验库两个大脑共享，一个踩的坑另一个也能避开。同一个坑别踩第二次。方法见 \`${ARCHIVE_NAME}/经验萃取方法论.md\`。

**第一次见面**：若你是新用户（根目录 \`${myFile}\` 的「我是谁」还是空模板），我开场给一个**可跳过的轻邀请**——想花一分钟认识下吗？不想就直接干活，我会边做边悄悄了解你。

**分寸**：不编造、不每轮汇报、一次性小任务不建项目记忆、经验要写清为什么和怎么用、敏感信息（密码密钥等）不主动写进记忆。完整机制随时可读 \`${ARCHIVE_NAME}/AI自我成长机制.md\`。
${MD_END}`;
}

// 把指令块幂等写入指定文件（不存在就新建、已有旧块先删再写、绝不动用户其它内容）
function writeMd(targetPath, blockText) {
  let cur = '';
  try { cur = fs.readFileSync(targetPath, 'utf8'); } catch (_) { cur = ''; }
  const re = mdRe();
  cur = cur.replace(re, '').replace(/\n{3,}/g, '\n\n').trim();
  const next = (cur ? cur + '\n\n' : '') + blockText + '\n';
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  fs.writeFileSync(targetPath, next);
}

// ---------- 对单个知识库安装 ----------
function installToVault(vaultDir, coreDir) {
  const archiveDir = path.join(vaultDir, ARCHIVE_NAME);
  const brainSrc = path.join(coreDir, '成长大脑');
  const memSrc = path.join(coreDir, '记忆模板');

  // 1) 成长大脑：覆盖式刷新（产品文档）
  copyDir(brainSrc, archiveDir);
  ok(`${path.basename(vaultDir)}：已安装「成长大脑」到 ${ARCHIVE_NAME}/`);

  // 2) 记忆文件：绝不覆盖已有（用户的记忆是资产）
  let added = 0, kept = 0;
  for (const ent of fs.readdirSync(memSrc, { withFileTypes: true })) {
    if (!ent.isFile()) continue;
    const wrote = copyFileKeep(path.join(memSrc, ent.name), path.join(archiveDir, ent.name));
    if (wrote) added++; else kept++;
  }
  if (added) ok(`  新建 ${added} 个记忆文件（经验库/项目记忆模板）`);
  if (kept) info(`  保留 ${kept} 个已存在的记忆文件（没动你已积累的内容）`);

  // 3) 指令块：CLAUDE.md（给 Claude）+ AGENTS.md（给 GPT）—— 一个知识库两个大脑都会成长
  writeMd(path.join(vaultDir, 'CLAUDE.md'), mdBlock('Claude', 'CLAUDE.md', 'AGENTS.md'));
  writeMd(path.join(vaultDir, 'AGENTS.md'), mdBlock('GPT', 'AGENTS.md', 'CLAUDE.md'));
  ok(`  已写入自我成长指令到该知识库的 CLAUDE.md（Claude）和 AGENTS.md（GPT）`);
}

// ---------- 卸载（只去指令；成长档案保留，那是用户记忆）----------
function uninstall() {
  const re = mdRe();
  const stripMd = (file) => {
    try {
      let cur = fs.readFileSync(file, 'utf8');
      if (!re.test(cur)) return false;
      re.lastIndex = 0;
      cur = cur.replace(re, '').replace(/\n{3,}/g, '\n\n').trim() + '\n';
      fs.writeFileSync(file, cur);
      return true;
    } catch (_) { return false; }
  };
  let n = 0;
  for (const vd of findVaultDirs()) {
    const a = stripMd(path.join(vd, 'CLAUDE.md'));
    const b = stripMd(path.join(vd, 'AGENTS.md'));
    if (a || b) n++;
  }
  if (n) ok(`已从 ${n} 个知识库的 CLAUDE.md 和 AGENTS.md 移除自我成长指令`);
  warn(`各知识库的 ${ARCHIVE_NAME}/ 文件夹**未删除**——里面是你积累的记忆（画像/经验/项目）。如确需删除，请手动删。`);
  console.log(`\n${C.g}AI 自我成长工具已卸载（记忆已为你保留）。${C.n}\n`);
}

// ---------- 安装 ----------
function install(coreDir) {
  if (!coreDir || !fs.existsSync(coreDir)) {
    console.error(`${C.r}找不到核心目录：${coreDir}${C.n}`);
    console.error('用法：node install-core.js <这个文件夹里的「核心」目录>');
    process.exit(1);
  }
  if (!fs.existsSync(path.join(coreDir, '成长大脑')) || !fs.existsSync(path.join(coreDir, '记忆模板'))) {
    console.error(`${C.r}核心目录不完整（缺「成长大脑」或「记忆模板」）：${coreDir}${C.n}`);
    process.exit(1);
  }

  const vaultDirs = findVaultDirs();
  if (vaultDirs.length === 0) {
    warn('没找到 Obsidian 知识库。请确认 Obsidian 装好、至少打开过一个知识库后再装。');
    console.error(`${C.r}未安装（找不到知识库）。${C.n}`);
    process.exit(1);
  }

  for (const vd of vaultDirs) installToVault(vd, coreDir);

  console.log(`\n${C.g}========================================${C.n}`);
  console.log(`${C.g}  🌱 AI 自我成长工具安装成功！${C.n}`);
  console.log(`${C.g}========================================${C.n}`);
  console.log(`\n  装进了 ${vaultDirs.length} 个知识库的「${ARCHIVE_NAME}/」文件夹。`);
  console.log(`  ${C.b}下一步：${C.n}新开一个对话（指令要新会话才生效）。Claude 和 GPT 两个大脑都会开始成长。`);
  console.log(`  之后正常用就行——不管你用哪个大脑，它都会在帮你干活的过程中越来越懂你。\n`);
}

// ---------- 入口 ----------
const args = process.argv.slice(2);
try {
  if (args.includes('--uninstall')) {
    uninstall();
  } else {
    const coreDir = args.find(a => !a.startsWith('--')) || path.dirname(__filename);
    install(path.resolve(coreDir));
  }
} catch (e) {
  console.error(`${C.r}安装出错：${e.message}${C.n}`);
  console.error('可以把这段报错发给你的 AI 助手，让它帮你修。');
  process.exit(1);
}
