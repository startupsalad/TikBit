'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

function readJson(file) {
  try {
    const value = JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error();
    return value;
  } catch { throw new Error('本机 JSON 配置无法解析；请检查文件格式，不会输出原始内容。'); }
}
function trustedBase(raw) {
  try {
    const u = new URL(raw);
    if (u.protocol !== 'https:' || u.hostname !== 'tikbit.ai' || u.port || u.username || u.password || u.search || u.hash) return null;
    if (!['', '/', '/v1', '/v1/'].includes(u.pathname)) return null;
    return 'https://tikbit.ai/v1';
  } catch { return null; }
}
function parseEnvironment(text) {
  const out = {};
  for (const line of String(text || '').split(/\r?\n/)) {
    const m = line.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z_0-9]*)\s*=\s*(.*?)\s*$/);
    if (!m) continue;
    let value = m[2];
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1,-1);
    out[m[1]] = value;
  }
  return out;
}
function runtimePair(env) {
  for (const [key, base] of [[env.ANTHROPIC_AUTH_TOKEN || env.ANTHROPIC_API_KEY, env.ANTHROPIC_BASE_URL], [env.OPENAI_API_KEY, env.OPENAI_BASE_URL]]) {
    const url = trustedBase(base);
    if (key && url) return { api_key: key, base_url: url };
  }
  return null;
}
function resolveCredentials(config = {}, env = process.env, {home = os.homedir()} = {}) {
  const key = env.GPT_API_KEY || config.api_key;
  const base = env.GPT_BASE_URL || config.base_url;
  // An explicit user image key is never sent to an inferred endpoint.
  if (key) {
    if (!base) throw new Error('生图配置缺少 base_url；请在本机设置 GPT_BASE_URL。不要在聊天中发送密钥。');
    let u;
    try { u = new URL(base); } catch { throw new Error('生图配置 base_url 无效。'); }
    if (!['https:', 'http:'].includes(u.protocol) || u.username || u.password || u.search || u.hash) throw new Error('生图配置 base_url 无效。');
    return {api_key: String(key), base_url: String(base).replace(/\/+$/, ''), credential_source: env.GPT_API_KEY ? 'image-environment' : 'image-config'};
  }
  // A blank example uses the trusted TikBit URL; a custom URL must have its own key.
  if (base && !trustedBase(base)) throw new Error('生图配置为自定义网址，但缺少专用密钥；不会向此网址发送工作台令牌。');
  const inherited = runtimePair(env);
  if (inherited) return {...inherited, credential_source:'workstation-environment'};
  const refFile = path.join(home, '.tikbit/gpt-image/workstation.json');
  if (fs.existsSync(refFile)) {
    let refs;
    try { refs = readJson(refFile); } catch { throw new Error('生图工作台引用配置损坏，请运行本地生图修复入口。'); }
    const matches = [];
    for (const file of Array.isArray(refs.settings) ? refs.settings : []) {
      if (typeof file !== 'string' || !path.isAbsolute(file)) continue;
      if (!fs.existsSync(file)) continue;
      let data;
      try { data = readJson(file); } catch { throw new Error('工作台配置损坏，未读取或输出其中的密钥。'); }
      for (const id of ['claude', 'codex']) {
        const pair = runtimePair(parseEnvironment(data.providerConfigs?.[id]?.environmentVariables));
        if (pair) matches.push({...pair, credential_source:'workstation-reference'});
      }
    }
    const unique = [...new Map(matches.map(x => [x.base_url+'\n'+x.api_key, x])).values()];
    if (unique.length === 1) return unique[0];
    if (unique.length > 1) throw new Error('多个工作台凭据不一致；请从目标库的 AI 对话执行，或在本机设置专用 GPT_API_KEY/GPT_BASE_URL。');
  }
  throw new Error('生图配置未就绪：请在目标工作台对话内执行，或运行生图修复入口选择知识库。自定义服务请在本机设置 GPT_API_KEY 与 GPT_BASE_URL；不要将密钥贴到聊天。');
}
module.exports = { readJson, trustedBase, parseEnvironment, resolveCredentials };
