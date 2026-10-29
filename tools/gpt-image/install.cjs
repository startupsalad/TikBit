#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {readJson} = require('./image-config.cjs');
function assertNoLinks(file) {
  for (let p=path.resolve(file);;p=path.dirname(p)) {
    try { if (fs.lstatSync(p).isSymbolicLink()) throw new Error('拒绝覆盖链接路径，请人工确认工具目录。'); }
    catch(e) { if (e.code !== 'ENOENT') throw e; }
    if (path.dirname(p)===p) break;
  }
}
function settingsForVault(vault) {
  if (!path.isAbsolute(vault)) throw new Error('请选择知识库的完整路径。');
  const files=[];
  for (const d of fs.readdirSync(vault,{withFileTypes:true})) {
    if (!d.isDirectory()) continue;
    const pluginDir=path.join(vault,d.name,'plugins/tikbit-claudian');
    if (!fs.existsSync(pluginDir)) continue;
    const plugin=path.join(pluginDir,'data.json');
    const data=fs.existsSync(plugin)?readJson(plugin):{};
    const folder=Object.hasOwn(data,'dataFolder') ? String(data.dataFolder).trim() : '.claudian';
    if (!/^\.[^\\/:\x00-\x1f]+$/.test(folder) || folder==='..' || folder.toLowerCase()===d.name.toLowerCase() || folder.toLowerCase()==='.obsidian') throw new Error('知识库的 TikBit 数据目录无效。');
    const file=path.join(vault,folder,'claudian-settings.json');
    assertNoLinks(file);
    if (fs.existsSync(file)) files.push(file);
  }
  if (files.length>1) throw new Error('此库有多个 TikBit 配置；请从目标库的 AI 对话执行生图。');
  return files;
}
function discover(home, platform=process.platform, appData=process.env.APPDATA) {
  const root=platform==='darwin' ? path.join(home,'Library/Application Support') : (appData || path.join(home,'AppData/Roaming'));
  const file=path.join(root,'obsidian/obsidian.json');
  if (!fs.existsSync(file)) return [];
  return Object.values(readJson(file).vaults || {}).map(v=>v.path).filter(v=>typeof v==='string' && path.isAbsolute(v) && fs.existsSync(v));
}
function install({home=os.homedir(), source=__dirname, vaults=[], discoverVaults=false, platform=process.platform, appData}={}) {
  if (!path.isAbsolute(home)) throw new Error('用户目录必须是绝对路径。');
  const target=path.join(home,'.tikbit/gpt-image'), cfg=path.join(target,'config.json'), refs=path.join(target,'workstation.json');
  const names=['gpt-image.js','image-config.cjs','install.cjs','SKILL.md','VERSION','config.example.json'];
  const selected=[...new Set(vaults.concat(discoverVaults?discover(home,platform,appData):[]))];
  const settings=selected.flatMap(settingsForVault);
  // Preflight every source, user JSON and destination before writing anything.
  const old=fs.existsSync(refs)?readJson(refs):{settings:[]};
  if (fs.existsSync(cfg)) readJson(cfg);
  const destinations=[target,cfg,refs,...names.map(n=>path.join(target,n))];
  for (const e of ['claude','codex']) destinations.push(path.join(home,'.tikbit',e,'skills/gpt-image/SKILL.md'));
  for (const p of destinations) assertNoLinks(p);
  for (const n of names) if (!fs.statSync(path.join(source,n)).isFile()) throw new Error('安装包缺少生图文件：'+n);
  fs.mkdirSync(target,{recursive:true,mode:0o700});
  for (const n of names) {
    const src=path.join(source,n), dst=path.join(target,n);
    if (path.resolve(src)!==path.resolve(dst)) fs.copyFileSync(src,dst);
  }
  if (!fs.existsSync(cfg)) fs.writeFileSync(cfg,JSON.stringify({api_key:'',base_url:'https://tikbit.ai/v1',image_model:'gpt-image-2.5-sunburst',output_dir:''},null,2)+'\n',{flag:'wx',mode:0o600});
  const all=[...new Set([...(Array.isArray(old.settings)?old.settings:[]),...settings])];
  fs.writeFileSync(refs,JSON.stringify({settings:all},null,2)+'\n',{mode:0o600});
  for (const e of ['claude','codex']) {
    const dst=path.join(home,'.tikbit',e,'skills/gpt-image'); fs.mkdirSync(dst,{recursive:true});
    fs.copyFileSync(path.join(target,'SKILL.md'),path.join(dst,'SKILL.md'));
  }
  return {installed:true, vaults:settings.length};
}
module.exports={install, settingsForVault, discover};
if (require.main===module) {
  try {
    const args=process.argv.slice(2), vaults=[];
    for (let i=0;i<args.length;i++) {
      if (args[i]==='--vault' && args[i+1]) vaults.push(path.resolve(args[++i]));
      else if (args[i]!=='--discover') throw new Error('用法：node install.cjs [--vault 知识库路径] [--discover]');
    }
    const result=install({vaults,discoverVaults:args.includes('--discover')});
    console.log(`生图工具和双引擎 Skill 已修复，登记 ${result.vaults} 个工作台配置；原密钥、模型、输出图片保持不变。重新开启 AI 对话后生效。`);
  } catch { console.error('生图修复失败：请检查工具包是否完整、目录是否可写、用户 JSON 配置是否有效；原配置不会被重置。'); process.exitCode=1; }
}
