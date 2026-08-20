#!/usr/bin/env node
/* ============================================================================
 * 创业沙拉 AI 工作台 · GPT 生图工具（跨平台 Mac / Windows，零依赖 Node 版）
 * ----------------------------------------------------------------------------
 * 功能：
 *   1) 文字生图：输入 prompt 生成图片
 *   2) 参考图编辑：基于一张或多张参考图修改（换风格 / 换背景 / 合成）
 *   3) 批量并发：一次生成多张（内置并发上限，不用手写脚本循环）
 *
 * 为什么用 Node：AI 工作台已自带便携 Node，零依赖、双击即用；
 *   不依赖 Python（干净 Mac 默认不带 python3，会卡安装）。
 *
 * 用法：
 *   # 文字生图
 *   node gpt-image.js "一只可爱的柴犬" --size 1024x1024 --output 柴犬
 *
 *   # 参考图编辑（一张或多张，逗号分隔）
 *   node gpt-image.js "改成赛博朋克风格" --reference 原图.png
 *   node gpt-image.js "把两张图合成一张" --reference 图1.png,图2.png
 *
 *   # 批量并发（做多张时推荐；并发上限默认 3，避免打爆上游）
 *   node gpt-image.js --batch 任务清单.txt --concurrency 3
 *   # 任务清单.txt 每行一个任务，两种写法：
 *   #   输出文件名<Tab或 | >图片描述     （指定文件名）
 *   #   图片描述                          （自动按时间戳命名）
 *   #   以 # 开头是注释，空行忽略
 *
 * 输出：默认存到 ~/.tikbit/gpt-image/输出/；可在 config.json 改 output_dir 重定向。
 * 配置：~/.tikbit/gpt-image/config.json
 *      base_url / api_key / image_model / output_dir
 *      / read_timeout 读超时秒·默认300 / max_retries 重试次数·默认5
 *      / gateway_timeout_secs 慢5xx判定阈值·默认90 / gateway_max_retries 慢5xx最多重试·默认2
 *      环境变量 GPT_API_KEY / GPT_BASE_URL / GPT_READ_TIMEOUT / GPT_MAX_RETRIES
 *      / GPT_GATEWAY_TIMEOUT_SECS / GPT_GATEWAY_MAX_RETRIES 优先级更高。
 *
 * 稳定性设计（2026-07-03）：
 *   - 网关超时快速失败：上游生图 >~125s 会被它自家网关掐成 5xx（524/504等），
 *     每次白等一两分钟。工具识别"慢 5xx"（按耗时+状态码），这类最多再试
 *     gateway_max_retries 次（默认2）就放弃，不再耗满 max_retries。真正的多渠道
 *     切换应由中转站按优先级+自动禁用完成，脚本硬扛没意义。
 *   - 4xx 客户端错误（坏密钥/坏模型/坏参数）立即失败，不重试（429 限流除外）。
 *   - 批量并发默认 3（实测 5 并发易把单一上游打爆），单张失败不影响其它，
 *     结束打印成功/失败回执汇总。
 * ========================================================================== */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

// ── 路径 ────────────────────────────────────────────────
const PKG_DIR = path.join(os.homedir(), '.tikbit', 'gpt-image');
const CONFIG_FILE = path.join(PKG_DIR, 'config.json');
const DEFAULT_OUTPUT_DIR = path.join(PKG_DIR, '输出');

const C = { g: '\x1b[1;32m', y: '\x1b[1;33m', r: '\x1b[1;31m', b: '\x1b[1;36m', n: '\x1b[0m' };

const SIZES = ['1024x1024', '1536x1024', '1024x1536', '2048x2048',
  '2048x1152', '1152x2048', '3840x2160', '2160x3840'];

// 网关/上游超时类状态码：这类 5xx 多半是"上游生图太慢被网关掐"，重试同一路径意义不大
const GATEWAY_TIMEOUT_CODES = new Set([502, 503, 504, 520, 522, 524]);

// 明确的"立即失败"错误（4xx 客户端错误 / 快速失败），不参与重试、批量据此记账
class GenerationError extends Error {}

// ── API 缺失时的友好引导 ────────────────────────────────
function printNoApiHelp() {
  process.stderr.write(`
============================================================
⚠️  GPT 生图功能还没配置 API（首次使用，跟着提示走 1 分钟搞定）
============================================================

👉 最简单的方式：直接跟你的 AI 助手说一句：

   "我的 GPT API 网址是 https://tikbit.ai/v1
    密钥是 sk-yyy
    帮我填进生图配置"

AI 会自动帮你写进配置文件，然后你就能正常生图了。
你不需要自己打开任何文件、不需要懂代码。

------------------------------------------------------------
还没有 API？去「创业沙拉 AI 算力平台」新建一个（1 分钟）：

   1. 打开  https://tikbit.ai
   2. 新建一个 API 密钥（sk- 开头）
   3. ⭐ 务必确认这个 API 「包含 GPT 模型」（gpt-image 系列），
      否则只能生成文字、不能生图
   4. 把网址和密钥发给你的 AI，让它帮你填进配置

如果配置遇到问题，请联系你的 TikBit 工作台管理员，不要把密钥发到公开聊天或代码仓库。
============================================================
`);
}

// ── 读配置 ──────────────────────────────────────────────
function loadConfig() {
  const cfg = {
    base_url: '', api_key: '', image_model: 'gpt-image-2', output_dir: '',
    read_timeout: '300', max_retries: '5',
    gateway_timeout_secs: '90', gateway_max_retries: '2',
  };
  try {
    const j = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    for (const k of Object.keys(cfg)) {
      if (j[k] !== undefined && j[k] !== null) cfg[k] = String(j[k]);
    }
  } catch (_) { /* 没配置就走环境变量 / 引导 */ }

  if (process.env.GPT_API_KEY) cfg.api_key = process.env.GPT_API_KEY;
  if (process.env.GPT_BASE_URL) cfg.base_url = process.env.GPT_BASE_URL;
  if (process.env.GPT_READ_TIMEOUT) cfg.read_timeout = process.env.GPT_READ_TIMEOUT;
  if (process.env.GPT_MAX_RETRIES) cfg.max_retries = process.env.GPT_MAX_RETRIES;
  if (process.env.GPT_GATEWAY_TIMEOUT_SECS) cfg.gateway_timeout_secs = process.env.GPT_GATEWAY_TIMEOUT_SECS;
  if (process.env.GPT_GATEWAY_MAX_RETRIES) cfg.gateway_max_retries = process.env.GPT_GATEWAY_MAX_RETRIES;

  if (!cfg.api_key || !cfg.base_url) {
    printNoApiHelp();
    process.exit(1);
  }
  cfg.base_url = cfg.base_url.replace(/\/+$/, '');
  return cfg;
}

// ── 决定输出目录 ────────────────────────────────────────
function getOutputDir(cfg) {
  if (cfg.output_dir) {
    let p = cfg.output_dir;
    if (p.startsWith('~')) p = path.join(os.homedir(), p.slice(1));
    return p;
  }
  return DEFAULT_OUTPUT_DIR;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── 从 API 响应里取图片二进制（支持 b64_json 和 url 两种）──
async function extractImageBytes(data) {
  const item = data && data.data && data.data[0];
  if (!item) throw new Error(`响应格式异常：${JSON.stringify(data).slice(0, 200)}`);

  if (item.b64_json) {
    let b64 = item.b64_json;
    if (b64.startsWith('data:') && b64.includes(',')) b64 = b64.split(',')[1];
    // 修补缺失的 padding（部分中转站返回的 b64 可能不全）
    while (b64.length % 4) b64 += '=';
    const buf = Buffer.from(b64, 'base64');
    if (!buf.length) throw new Error(`base64 解码为空（响应可能被截断，长度=${b64.length}）`);
    return buf;
  }

  if (item.url) {
    for (let attempt = 1; attempt <= 5; attempt++) {
      try {
        process.stderr.write(`  📥 下载图片（尝试 ${attempt}/5）...\n`);
        const resp = await fetch(item.url, { signal: AbortSignal.timeout(120000) });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return Buffer.from(await resp.arrayBuffer());
      } catch (e) {
        if (attempt === 5) throw new Error(`下载图片失败（重试 5 次）：${e.message}`);
        process.stderr.write(`  ⚠️ 下载失败：${e.message}，2 秒后重试...\n`);
        await sleep(2000);
      }
    }
  }
  throw new Error(`响应格式异常：${JSON.stringify(item).slice(0, 200)}`);
}

// ── 带自动重试的 POST，成功条件 = 拿到有效图片 ──────────
// 最终失败抛异常（GenerationError=立即失败；Error=重试用尽），由调用方决定退出码/记账。
async function postForImage(url, cfg, { jsonBody = null, formBody = null, label = '' } = {}) {
  const headers = {
    'Authorization': `Bearer ${cfg.api_key}`,
    'User-Agent': 'curl/8.0',  // 部分中转站会拦截默认 UA
  };
  let body;
  if (jsonBody !== null) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(jsonBody);
  } else {
    body = formBody;  // FormData：fetch 自动带 multipart boundary
  }

  const timeoutMs = Math.max(1, Number(cfg.read_timeout) || 300) * 1000;
  const maxRetries = Math.max(1, Number(cfg.max_retries) || 5);
  const gatewaySecs = Math.max(1, Number(cfg.gateway_timeout_secs) || 90);
  const gatewayMax = Math.max(1, Number(cfg.gateway_max_retries) || 2);
  const tag = label ? `[${label}] ` : '';

  let lastErr = '';
  let slow5xx = 0;  // 累计遇到多少次"慢 5xx / 网关超时"
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const t0 = Date.now();
    let isGatewaySlow = false;
    try {
      const resp = await fetch(url, { method: 'POST', headers, body, signal: AbortSignal.timeout(timeoutMs) });
      if (resp.status >= 500) {
        const elapsed = (Date.now() - t0) / 1000;
        isGatewaySlow = GATEWAY_TIMEOUT_CODES.has(resp.status) || elapsed >= gatewaySecs;
        lastErr = `HTTP ${resp.status}（耗时${Math.round(elapsed)}s）${(await resp.text()).slice(0, 160)}`;
      } else if (resp.status === 429) {
        // 限流：上游一时忙，重试有意义
        lastErr = `HTTP 429 限流 ${(await resp.text()).slice(0, 120)}`;
      } else if (resp.status >= 400) {
        // 其它 4xx（401/403/400/404 等）：坏密钥/坏模型/坏参数，重试也没用，立即失败
        throw new GenerationError(`${tag}HTTP ${resp.status}（客户端错误，重试无用，立即失败）：${(await resp.text()).slice(0, 200)}`);
      } else {
        return await extractImageBytes(await resp.json());
      }
    } catch (e) {
      if (e instanceof GenerationError) throw e;  // 立即失败，不重试
      // 读超时=已连上、上游还在生图但迟迟没返回完整图 —— 视为慢链路
      if (e.name === 'TimeoutError') {
        isGatewaySlow = true;
        lastErr = `读超时（等了 ${Math.round(timeoutMs / 1000)}s 仍没收到完整图片，上游偏慢可加长 GPT_READ_TIMEOUT=480）`;
      } else {
        lastErr = e.message || String(e);
      }
    }

    // ── 网关超时快速失败：这类重试同一路径基本白等，攒够 gatewayMax 次就放弃 ──
    if (isGatewaySlow) {
      slow5xx += 1;
      if (slow5xx >= gatewayMax) {
        throw new GenerationError(
          `${tag}上游网关超时，已快速失败（遇到 ${slow5xx} 次慢5xx/超时，不再傻等）。` +
          `这是上游/中转站的锅，应由中转站按优先级切换渠道。最后错误：${lastErr}`);
      }
    }

    if (attempt < maxRetries) {
      process.stderr.write(`  ⏳ ${tag}第${attempt}次失败（${lastErr.slice(0, 110)}），2 秒后重试...\n`);
      await sleep(2000);
    }
  }
  throw new Error(`${tag}重试 ${maxRetries} 次仍失败：${lastErr}`);
}

// ── 文字生图 ────────────────────────────────────────────
async function generate(prompt, size, cfg, label = '') {
  return postForImage(`${cfg.base_url}/images/generations`, cfg, {
    jsonBody: { model: cfg.image_model, prompt, n: 1, size }, label,
  });
}

// ── 参考图编辑（单图 / 多图）────────────────────────────
async function edit(prompt, size, refPaths, cfg, label = '') {
  const form = new FormData();
  form.append('model', cfg.image_model);
  form.append('prompt', prompt);
  form.append('n', '1');
  form.append('size', size);
  const field = refPaths.length > 1 ? 'image[]' : 'image';
  for (const p of refPaths) {
    if (!fs.existsSync(p)) throw new GenerationError(`参考图不存在：${p}`);
    const buf = fs.readFileSync(p);
    form.append(field, new Blob([buf], { type: 'image/png' }), path.basename(p));
  }
  return postForImage(`${cfg.base_url}/images/edits`, cfg, { formBody: form, label });
}

// ── 保存图片 ────────────────────────────────────────────
function saveImage(imgBytes, outputName, cfg) {
  let name = outputName;
  if (!name) {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    name = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}_${pad(d.getMilliseconds() % 1000)}.png`;
  } else if (!/\.(png|jpg|jpeg|webp)$/i.test(name)) {
    name += '.png';
  }

  // A path supplied with --output is an explicit destination.  The old code
  // always joined it to the default output directory, so project paths were
  // silently written under ~/.tikbit/gpt-image/输出 instead.
  const hasPath = path.isAbsolute(name) || name.includes('/') || name.includes('\\');
  const outPath = hasPath
    ? (path.isAbsolute(name) ? name : path.resolve(process.cwd(), name))
    : path.join(getOutputDir(cfg), name);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, imgBytes);
  return outPath;
}

// ── 生成并保存一张（单张/批量共用，绝不抛出）──────────
async function runOne(prompt, outputName, size, refPaths, cfg, label = '') {
  const t0 = Date.now();
  try {
    const img = refPaths
      ? await edit(prompt, size, refPaths, cfg, label)
      : await generate(prompt, size, cfg, label);
    const outPath = saveImage(img, outputName, cfg);
    return { ok: true, name: outputName || path.basename(outPath), path: outPath, seconds: (Date.now() - t0) / 1000, prompt };
  } catch (e) {
    return { ok: false, name: outputName || '(时间戳)', error: e.message || String(e), seconds: (Date.now() - t0) / 1000, prompt };
  }
}

// ── 解析批量清单：每行 `文件名<Tab或|>描述` 或 `描述`；# 注释、空行忽略 ──
function parseBatchFile(file) {
  const tasks = [];
  const text = fs.readFileSync(file, 'utf8');
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    let name = '', prompt = line;
    if (line.includes('\t')) { const i = line.indexOf('\t'); name = line.slice(0, i); prompt = line.slice(i + 1); }
    else if (line.includes('|')) { const i = line.indexOf('|'); name = line.slice(0, i); prompt = line.slice(i + 1); }
    name = name.trim(); prompt = prompt.trim();
    if (prompt) tasks.push({ name: name || null, prompt });
  }
  return tasks;
}

// ── 并发池：最多 concurrency 个同时跑 ──────────────────
async function runPool(items, concurrency, worker) {
  const results = new Array(items.length);
  let next = 0;
  async function lane() {
    while (next < items.length) {
      const i = next++;
      results[i] = await worker(items[i], i);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, lane));
  return results;
}

// ── 批量生图：并发 + 回执汇总，返回退出码 ──────────────
async function runBatch(tasks, size, refPaths, cfg, concurrency) {
  const total = tasks.length;
  concurrency = Math.max(1, Math.min(concurrency, total));
  console.log(`🎨 批量生成 ${total} 张，并发上限 ${concurrency}（避免打爆上游）...`);
  let done = 0;
  const results = await runPool(tasks, concurrency, async (task, i) => {
    const r = await runOne(task.prompt, task.name, size, refPaths, cfg, `${i + 1}/${total}`);
    done += 1;
    if (r.ok) console.log(`  ${C.g}✅${C.n} [${done}/${total}] ${r.name}  (${Math.round(r.seconds)}s)`);
    else console.log(`  ${C.r}❌${C.n} [${done}/${total}] ${r.name}  (${Math.round(r.seconds)}s) — ${r.error.slice(0, 120)}`);
    return r;
  });

  const ok = results.filter(r => r && r.ok);
  const bad = results.filter(r => r && !r.ok);
  console.log('\n' + '='.repeat(48));
  console.log(`📊 批量回执：成功 ${ok.length} / ${total}，失败 ${bad.length}`);
  if (ok.length) {
    console.log('✅ 成功：');
    for (const r of ok) console.log(`   ${r.path}`);
  }
  if (bad.length) {
    console.log('❌ 失败明细：');
    for (const r of bad) console.log(`   ${r.name}: ${r.error.slice(0, 140)}`);
    console.log('💡 多为上游/中转站网关超时（524等）。建议：降低并发、稍后重试，' +
      '或在中转站给该模型配多供应商+优先级+自动禁用做故障转移。');
  }
  console.log('='.repeat(48));
  return bad.length ? 1 : 0;
}

// ── 极简参数解析 ────────────────────────────────────────
function parseArgs(argv) {
  const out = { _: [], size: '1024x1024', output: null, reference: null, batch: null, concurrency: 3 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--size') out.size = argv[++i];
    else if (a === '--output' || a === '-o') out.output = argv[++i];
    else if (a === '--reference' || a === '-r') out.reference = argv[++i];
    else if (a === '--batch') out.batch = argv[++i];
    else if (a === '--concurrency') out.concurrency = Math.max(1, parseInt(argv[++i], 10) || 3);
    else out._.push(a);
  }
  return out;
}

function resolveRefs(reference) {
  if (!reference) return null;
  return reference.split(',').map(s => {
    let p = s.trim();
    if (p.startsWith('~')) p = path.join(os.homedir(), p.slice(1));
    return path.resolve(p);
  });
}

// ── 入口 ────────────────────────────────────────────────
async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!SIZES.includes(args.size)) {
    process.stderr.write(`${C.r}❌ 不支持的尺寸 ${args.size}，可选：${SIZES.join(' / ')}${C.n}\n`);
    process.exit(1);
  }
  const cfg = loadConfig();
  const refPaths = resolveRefs(args.reference);

  // ── 批量模式 ──
  if (args.batch) {
    let batchFile = args.batch;
    if (batchFile.startsWith('~')) batchFile = path.join(os.homedir(), batchFile.slice(1));
    if (!fs.existsSync(batchFile)) {
      process.stderr.write(`${C.r}❌ 批量清单文件不存在：${batchFile}${C.n}\n`);
      process.exit(1);
    }
    const tasks = parseBatchFile(batchFile);
    if (!tasks.length) {
      process.stderr.write(`${C.r}❌ 清单里没有有效任务（每行：文件名<Tab或|>描述，或仅描述）${C.n}\n`);
      process.exit(1);
    }
    process.exit(await runBatch(tasks, args.size, refPaths, cfg, args.concurrency));
  }

  // ── 单张模式 ──
  const prompt = args._.join(' ').trim();
  if (!prompt) {
    process.stderr.write('用法：node gpt-image.js "图片描述" [--size 1024x1024] [--output 文件名] [--reference 参考图.png]\n' +
      '      批量：node gpt-image.js --batch 任务清单.txt --concurrency 3\n');
    process.exit(1);
  }
  const mode = refPaths ? '编辑' : '生成';
  console.log(`🎨 ${mode}中：${prompt.slice(0, 60)}...`);
  const r = await runOne(prompt, args.output, args.size, refPaths, cfg);
  if (r.ok) {
    console.log(`${C.g}✅ 已保存：${r.path}${C.n}  (${Math.round(r.seconds)}s)`);
  } else {
    process.stderr.write(`${C.r}❌ 生成失败：${r.error}${C.n}\n`);
    process.exit(1);
  }
}

main().catch(e => {
  process.stderr.write(`${C.r}❌ 出错：${e.message}${C.n}\n`);
  process.exit(1);
});
