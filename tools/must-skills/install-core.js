#!/usr/bin/env node
/* ============================================================================
 * TikBit AI 工作台 · 必装技能包 · 核心安装器 install-core.js
 * ----------------------------------------------------------------------------
 * 跨平台一份逻辑。首选「把整个文件夹交给用户的 AI，让 AI 跑这个脚本」。
 *
 * 干的活：
 *   1) 把 7 个 skill 装到系统级 ~/.claude/skills/（全知识库通用）
 *      docx / xlsx / pptx / pdf（文档四件套）+ skill-creator + kb-retriever + defuddle
 *   2) 装一份便携 Python 到 ~/.claude/doc-python/（Mac 按 CPU 架构挑 arm64/x64；Win 直接拷）
 *      —— 文档四件套 + kb-retriever 的脚本要用它，自带一份、绝不碰用户系统 Python，
 *         装没装 Python 都能用、零冲突、不弹开发者工具下载框。
 *   3) 往全局 + 各 Obsidian 知识库的 CLAUDE.md 追加行为指令：
 *      教 AI「跑这几个文档 skill 的脚本时，用便携 Python 那个绝对路径」。
 *
 * 用法：
 *   node install-core.js <这个文件夹里的「核心」目录>   # 安装
 *   node install-core.js --uninstall                    # 卸载
 * ========================================================================== */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const CLAUDE_DIR = path.join(HOME, '.claude');
const CODEX_DIR = path.join(HOME, '.codex');
const SKILLS_DIR = path.join(CLAUDE_DIR, 'skills');         // Claude 系统级 skill 目录
const CODEX_SKILLS_DIR = path.join(CODEX_DIR, 'skills');    // GPT(Codex) 系统级 skill 目录（格式同 Claude）
const DOC_PY_DIR = path.join(CLAUDE_DIR, 'doc-python');     // 便携 Python 安装目标（两个大脑共用这一份解释器路径）
const CLAUDE_MD = path.join(CLAUDE_DIR, 'CLAUDE.md');       // 全局·Claude 读
const CODEX_MD = path.join(CODEX_DIR, 'AGENTS.md');         // 全局·GPT(Codex) 读
const IS_WIN = process.platform === 'win32';
let PY_EXE = IS_WIN ? 'python' : 'python3';

// 包里带的 7 个 skill
const SKILLS = ['docx', 'xlsx', 'pptx', 'pdf', 'skill-creator', 'kb-retriever', 'defuddle'];
// 其中需要便携 Python 才能跑脚本的（文档四件套 + kb-retriever）
const PY_SKILLS = ['docx', 'xlsx', 'pptx', 'pdf', 'kb-retriever'];

const C = { g: '\x1b[1;32m', y: '\x1b[1;33m', r: '\x1b[1;31m', b: '\x1b[1;36m', n: '\x1b[0m' };
const ok = m => console.log(`${C.g}  ✓${C.n} ${m}`);
const info = m => console.log(`${C.b}  ·${C.n} ${m}`);
const warn = m => console.log(`${C.y}  !${C.n} ${m}`);

function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch (_) { return null; }
}

// ---------- 递归复制目录 ----------
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

// ---------- 1) 装 7 个 skill 到 ~/.claude/skills/ 和 ~/.codex/skills/（覆盖刷新，两个大脑通用）----------
// Codex 和 Claude 用同一套 Agent Skills 标准（SKILL.md），同一份 skill 文件夹装两处即可。
function installSkills(coreDir) {
  const skillSrcRoot = path.join(coreDir, 'skills');
  if (!fs.existsSync(skillSrcRoot)) {
    console.error(`${C.r}核心目录不完整，找不到 skills/：${coreDir}${C.n}`);
    process.exit(1);
  }
  fs.mkdirSync(SKILLS_DIR, { recursive: true });
  fs.mkdirSync(CODEX_SKILLS_DIR, { recursive: true });
  let n = 0;
  for (const name of SKILLS) {
    const src = path.join(skillSrcRoot, name);
    if (!fs.existsSync(src)) { warn(`包内缺少 skill「${name}」，跳过`); continue; }
    for (const root of [SKILLS_DIR, CODEX_SKILLS_DIR]) {
      const dst = path.join(root, name);
      fs.rmSync(dst, { recursive: true, force: true });   // 覆盖刷新为本包版本
      copyDir(src, dst);
    }
    n++;
  }
  ok(`已装 ${n} 个 skill 到 ~/.claude/skills/ 和 ~/.codex/skills/（docx/xlsx/pptx/pdf/skill-creator/kb-retriever/defuddle，两个大脑都能用）`);
}

// ---------- 2) 装便携 Python 到 ~/.claude/doc-python/ ----------
function installPython(coreDir) {
  let pySrc;
  if (IS_WIN) {
    pySrc = path.join(coreDir, 'python');
  } else {
    pySrc = path.join(coreDir, `python-${process.arch}`);   // python-arm64 / python-x64
    if (!fs.existsSync(pySrc)) {
      const alt = path.join(coreDir, 'python');
      if (fs.existsSync(alt)) pySrc = alt;
    }
  }
  if (fs.existsSync(pySrc)) {
    PY_EXE = IS_WIN
      ? path.join(DOC_PY_DIR, 'python.exe')
      : path.join(DOC_PY_DIR, 'bin', 'python3');
    fs.rmSync(DOC_PY_DIR, { recursive: true, force: true });  // 覆盖旧的，避免架构残留
    fs.cpSync(pySrc, DOC_PY_DIR, { recursive: true });
    if (!IS_WIN) {
      try { fs.chmodSync(PY_EXE, 0o755); } catch (_) {}
      try {
        const binDir = path.join(DOC_PY_DIR, 'bin');
        for (const f of fs.readdirSync(binDir)) {
          if (f.startsWith('python') || f === 'pip' || f.startsWith('pip3')) {
            try { fs.chmodSync(path.join(binDir, f), 0o755); } catch (_) {}
          }
        }
      } catch (_) {}
    }
    ok(`已装便携 Python（${IS_WIN ? 'win-x64' : process.arch}）`);
    return;
  }

  // Git 源码分发不携带 244MB 的平台 Python，改用用户已有解释器。
  const candidates = IS_WIN ? ['python', 'py'] : ['python3', 'python'];
  for (const cmd of candidates) {
    const probe = require('child_process').spawnSync(cmd, ['-c', 'import sys; print(sys.executable)'], { encoding: 'utf8' });
    if (probe.status === 0 && probe.stdout.trim()) {
      PY_EXE = probe.stdout.trim();
      ok(`使用本机 Python：${PY_EXE}`);
      return;
    }
  }
  warn('未找到 Python；文档类 skill 仍已安装，首次运行 docx/xlsx/pptx/pdf/kb-retriever 前请先安装 Python 3。');
}

// ---------- 3) CLAUDE.md 行为指令（带唯一标记，重复装不叠加）----------
// ★ MD_ID 是品牌无关的内部 ID，永不改。清理正则只锚定它，不锚品牌名，
//   这样带任何历史品牌名的旧块（旧品牌名/新品牌名/未来任何名字）都能被认出来正常替换/删除。
//   反面教材：曾用 esc(MD_BEGIN) 把品牌名整串锚进正则 → 改名后老用户重装叠出重复块、卸载删不掉。
const MD_ID = 'MUSTSKILLS';
const MD_BEGIN = `<!-- ${MD_ID}-BEGIN TikBit必装技能包·勿删此标记 -->`;
const MD_END = `<!-- ${MD_ID}-END -->`;
const mdRe = () => new RegExp('<!--\\s*' + MD_ID + '-BEGIN[\\s\\S]*?' + MD_ID + '-END\\s*-->', 'g');

function mdBlock(agent) {
  // 把本机解析出来的绝对路径直接写进指令，AI 无需再猜
  const pyPath = PY_EXE;
  return `${MD_BEGIN}
## 🧰 必装技能包（TikBit AI 工作台）

我（${agent}）装了「必装技能包」，多了这些看家本领（Claude 和 GPT 两个大脑各自的 skills 目录里都装了这套）。请遵守：

1. **文档四件套用便携 Python 跑**：当我用 \`docx\` / \`xlsx\` / \`pptx\` / \`pdf\` / \`kb-retriever\` 这几个 skill 里的 Python 脚本时，**一律用这个便携解释器，绝不用系统 python3**：
   \`\`\`
   ${pyPath}
   \`\`\`
   例：\`"${pyPath}" 某脚本.py 参数\`。它已预装好 python-docx / openpyxl / python-pptx / pypdf / pdfplumber / reportlab / pandas 等依赖，开箱即用。
2. **缺依赖就装进这份便携 Python**：万一某个库没带，用 \`"${pyPath}" -m pip install 包名\` 装进它自己，**不要动用户系统的 Python**。
3. **能力边界（诚实告知用户）**：扫描件 OCR（pytesseract）、部分 PDF→图片/Office→PDF 转换需要额外的系统程序（tesseract / poppler / LibreOffice），便携 Python 里没有。遇到这类需求时先告诉用户"这步需要额外装 XX"，不要硬跑报错。常规的读/写/改/合并/拆分/填表都能直接做。
4. **各 skill 用途**：docx=Word 文档、xlsx=Excel 表格与公式图表、pptx=PPT、pdf=读/合并/拆分/填表/生成 PDF、skill-creator=帮用户造新 skill、kb-retriever=在本地知识库里检索问答、defuddle=把网页正文抓成干净 Markdown。
${MD_END}`;
}

function writeMd(targetPath, agent) {
  let cur = '';
  try { cur = fs.readFileSync(targetPath, 'utf8'); } catch (_) { cur = ''; }
  const re = mdRe();
  cur = cur.replace(re, '').replace(/\n{3,}/g, '\n\n').trim();
  const next = (cur ? cur + '\n\n' : '') + mdBlock(agent) + '\n';
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  fs.writeFileSync(targetPath, next);
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

// ---------- 卸载 ----------
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
  if (stripMd(CLAUDE_MD)) n++;
  if (stripMd(CODEX_MD)) n++;
  for (const vd of findVaultDirs()) {
    if (stripMd(path.join(vd, 'CLAUDE.md'))) n++;
    if (stripMd(path.join(vd, 'AGENTS.md'))) n++;
  }
  if (n) ok(`已从 ${n} 处 CLAUDE.md / AGENTS.md 移除必装技能包指令`);

  // 删便携 Python（我们的东西，可放心删）
  try { fs.rmSync(DOC_PY_DIR, { recursive: true, force: true }); ok('已删除 ~/.claude/doc-python/'); } catch (_) {}

  // skill 不自动删：它们是通用能力、地基包/其它工具可能也在用，留着无害
  warn('7 个 skill 未自动删除（通用能力，可能别处也在用）。如确需删除，手动删 ~/.claude/skills/ 和 ~/.codex/skills/ 下对应目录。');
  console.log(`\n${C.g}必装技能包已卸载。${C.n}\n`);
}

// ---------- 安装 ----------
function install(coreDir) {
  if (!coreDir || !fs.existsSync(coreDir)) {
    console.error(`${C.r}找不到核心目录：${coreDir}${C.n}`);
    console.error('用法：node install-core.js <这个文件夹里的「核心」目录>');
    process.exit(1);
  }
  const vaultDirs = findVaultDirs();

  installSkills(coreDir);
  installPython(coreDir);

  writeMd(CLAUDE_MD, 'Claude');
  writeMd(CODEX_MD, 'GPT');
  ok('已写入行为指令到全局 ~/.claude/CLAUDE.md（Claude）和 ~/.codex/AGENTS.md（GPT）');
  let vn = 0;
  for (const vd of vaultDirs) {
    try {
      writeMd(path.join(vd, 'CLAUDE.md'), 'Claude');
      writeMd(path.join(vd, 'AGENTS.md'), 'GPT');
      vn++;
    } catch (_) {}
  }
  if (vn) ok(`已写入指令到 ${vn} 个知识库的 CLAUDE.md（Claude）和 AGENTS.md（GPT）`);
  else info('没找到 Obsidian 知识库；正常用就会读到全局指令');

  console.log(`\n${C.g}========================================${C.n}`);
  console.log(`${C.g}  🧰 必装技能包安装成功！${C.n}`);
  console.log(`${C.g}========================================${C.n}`);
  console.log(`\n  ${C.b}下一步：${C.n}新开一个对话（指令要新会话才生效）。Claude 和 GPT 两个大脑都能用这些 skill。`);
  console.log(`  之后跟 AI 说「帮我做个 Word / Excel / PPT / PDF」，它会用自带的引擎直接产出。\n`);
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
