'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { resolveCredentials } = require('./image-config.cjs');
const { install } = require('./install.cjs');
const { loadConfig, saveImage, resolveModel } = require('./gpt-image.js');
function sandbox(t) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'tikbit-image-test-'));
  t.after(() => fs.rmSync(home, { recursive: true, force: true }));
  return home;
}
function json(file, data) { fs.mkdirSync(path.dirname(file), {recursive:true}); fs.writeFileSync(file, JSON.stringify(data)); }
const pair = { ANTHROPIC_AUTH_TOKEN: 'synthetic-workbench-token', ANTHROPIC_BASE_URL: 'https://tikbit.ai' };
test('paired TikBit runtime credentials normalize /v1', () => {
  const x = resolveCredentials({}, pair, {home:'/unused'});
  assert.equal(x.api_key, pair.ANTHROPIC_AUTH_TOKEN); assert.equal(x.base_url, 'https://tikbit.ai/v1');
});
test('explicit image credentials have priority, including custom endpoints', () => {
  const x = resolveCredentials({api_key:'synthetic-custom',base_url:'https://example.invalid/v1'}, pair, {home:'/unused'});
  assert.equal(x.api_key,'synthetic-custom'); assert.equal(x.base_url,'https://example.invalid/v1');
});
test('never pair workstation key with explicit foreign destination', () => {
  assert.throws(() => resolveCredentials({base_url:'https://example.invalid/v1'}, pair, {home:'/unused'}), /配置|configuration/i);
});
test('reject incomplete or foreign workstation pairs without leaking tokens', () => {
  for (const env of [ {ANTHROPIC_AUTH_TOKEN:pair.ANTHROPIC_AUTH_TOKEN}, {...pair,ANTHROPIC_BASE_URL:'https://example.invalid'}, {...pair,ANTHROPIC_BASE_URL:'https://tikbit.ai.evil.invalid'}, {...pair,ANTHROPIC_BASE_URL:'http://tikbit.ai'} ]) {
    assert.throws(() => resolveCredentials({}, env, {home:'/unused'}), e => !e.message.includes(pair.ANTHROPIC_AUTH_TOKEN));
  }
});
test('Codex runtime pair supported without Claude token', () => {
  assert.equal(resolveCredentials({}, {OPENAI_API_KEY:'synthetic-codex',OPENAI_BASE_URL:'https://tikbit.ai/v1'}, {home:'/unused'}).api_key, 'synthetic-codex');
});
test('explicit GPT environment overrides explicit config', () => {
  const x = resolveCredentials({api_key:'old',base_url:'https://example.invalid/v1'}, {GPT_API_KEY:'new',GPT_BASE_URL:'https://other.invalid/v1'}, {home:'/unused'});
  assert.equal(x.api_key,'new'); assert.equal(x.base_url,'https://other.invalid/v1');
});
test('config model is preserved; Image 2 is not silently upgraded', t => {
  const home=sandbox(t); json(path.join(home,'.tikbit/gpt-image/config.json'),{api_key:'synthetic',base_url:'https://tikbit.ai/v1',image_model:'gpt-image-2-4K'});
  assert.equal(loadConfig({home,env:{}}).image_model,'gpt-image-2-4K');
  assert.equal(resolveModel('gpt-image-2'), 'gpt-image-2'); assert.equal(resolveModel('快速'),'gpt-image-2.5-flare');
});
test('Image 2.5 fine is the default while saved models and environment choices retain priority', t => {
  const home=sandbox(t), env={GPT_API_KEY:'synthetic-default-test',GPT_BASE_URL:'https://example.invalid/v1'};
  assert.equal(loadConfig({home,env}).image_model,'gpt-image-2.5-sunburst');
  const cfg=path.join(home,'.tikbit/gpt-image/config.json');
  json(cfg,{api_key:'synthetic-local',base_url:'https://example.invalid/v1'});
  assert.equal(loadConfig({home,env:{}}).image_model,'gpt-image-2.5-sunburst');
  json(cfg,{api_key:'synthetic-local',base_url:'https://example.invalid/v1',image_model:'gpt-image-2'});
  assert.equal(loadConfig({home,env:{}}).image_model,'gpt-image-2');
  assert.equal(loadConfig({home,env:{GPT_IMAGE_MODEL:'快速'}}).image_model,'gpt-image-2.5-flare');
  assert.equal(resolveModel('精细'),'gpt-image-2.5-sunburst');
});
test('fresh install puts executable at canonical path and resident skills in both engines', t => {
  const home=sandbox(t); install({home});
  assert.ok(fs.existsSync(path.join(home,'.tikbit/gpt-image/gpt-image.js')));
  for (const e of ['claude','codex']) assert.ok(fs.existsSync(path.join(home,'.tikbit',e,'skills/gpt-image/SKILL.md')));
  const cfg=JSON.parse(fs.readFileSync(path.join(home,'.tikbit/gpt-image/config.json'))); assert.equal(cfg.api_key,''); assert.equal(cfg.image_model,'gpt-image-2.5-sunburst');
});
test('repeat install preserves user config, output and old nested install', t => {
  const home=sandbox(t); const base=path.join(home,'.tikbit/gpt-image'); json(path.join(base,'config.json'),{api_key:'synthetic-user',output_dir:'keep',image_model:'custom'});
  fs.mkdirSync(path.join(base,'输出'),{recursive:true}); fs.writeFileSync(path.join(base,'输出/keep.png'),'original');
  const legacy=path.join(home,'.tikbit/tools/gpt-image/gpt-image/gpt-image.js'); fs.mkdirSync(path.dirname(legacy),{recursive:true}); fs.writeFileSync(legacy,'legacy');
  const before=fs.readFileSync(path.join(base,'config.json')); install({home}); install({home});
  assert.deepEqual(fs.readFileSync(path.join(base,'config.json')),before); assert.equal(fs.readFileSync(path.join(base,'输出/keep.png'),'utf8'),'original'); assert.equal(fs.readFileSync(legacy,'utf8'),'legacy');
});
test('repair registers selected vault without copying secrets; reads live rotation', t => {
  const home=sandbox(t), vault=path.join(home,'vault'), plugin=path.join(vault,'.obsidian/plugins/tikbit-claudian/data.json'); json(plugin,{dataFolder:'.custom-data'});
  const settings=path.join(vault,'.custom-data/claudian-settings.json');
  json(settings,{providerConfigs:{claude:{environmentVariables:'ANTHROPIC_AUTH_TOKEN=synthetic-one\nANTHROPIC_BASE_URL=https://tikbit.ai'}}});
  install({home,vaults:[vault]});
  const refs=fs.readFileSync(path.join(home,'.tikbit/gpt-image/workstation.json'),'utf8'); assert.ok(!refs.includes('synthetic-one'));
  assert.equal(resolveCredentials({}, {}, {home}).api_key,'synthetic-one');
  json(settings,{providerConfigs:{claude:{environmentVariables:'ANTHROPIC_AUTH_TOKEN=synthetic-two\nANTHROPIC_BASE_URL=https://tikbit.ai'}}});
  assert.equal(resolveCredentials({}, {}, {home}).api_key,'synthetic-two');
});
test('malformed user config is rejected without overwrite', t => {
  const home=sandbox(t), file=path.join(home,'.tikbit/gpt-image/config.json'); fs.mkdirSync(path.dirname(file),{recursive:true}); fs.writeFileSync(file,'broken');
  assert.throws(()=>install({home}),/config|配置/i); assert.equal(fs.readFileSync(file,'utf8'),'broken');
});
test('generated output never overwrites an existing image', t => {
  const home=sandbox(t), cfg={output_dir:home}; const a=saveImage(Buffer.from('first'),'keep',cfg), b=saveImage(Buffer.from('second'),'keep',cfg);
  assert.notEqual(a,b); assert.equal(fs.readFileSync(a,'utf8'),'first'); assert.equal(fs.readFileSync(b,'utf8'),'second');
});
test('--check does not generate images or expose credentials', t => {
  const home=sandbox(t); install({home});
  const out=spawnSync(process.execPath,[path.join(home,'.tikbit/gpt-image/gpt-image.js'),'--check'],{encoding:'utf8',env:{...process.env,USERPROFILE:home,HOME:home,GPT_API_KEY:'synthetic-check-secret',GPT_BASE_URL:'https://example.invalid/v1'}});
  assert.equal(out.status,0, out.stderr); assert.ok(!out.stdout.includes('synthetic-check-secret')); assert.ok(!fs.existsSync(path.join(home,'.tikbit/gpt-image/输出')));
});

test('repair supports custom config directories and trimmed data folder', t => {
 const home=sandbox(t), vault=path.join(home,'vault'); json(path.join(vault,'.obsidian-work/plugins/tikbit-claudian/data.json'),{dataFolder:' .work-data '});
 json(path.join(vault,'.work-data/claudian-settings.json'),{providerConfigs:{codex:{environmentVariables:'OPENAI_API_KEY=synthetic-custom-folder\nOPENAI_BASE_URL=https://tikbit.ai/v1'}}});
 install({home,vaults:[vault]}); assert.equal(resolveCredentials({}, {}, {home}).api_key,'synthetic-custom-folder');
});
test('ambiguous vault credentials fail instead of picking another account', t=>{
 const home=sandbox(t), refs=[];
 for(let i=0;i<2;i++){const file=path.join(home,'vault'+i,'settings.json'); json(file,{providerConfigs:{claude:{environmentVariables:'ANTHROPIC_AUTH_TOKEN=synthetic-'+i+'\nANTHROPIC_BASE_URL=https://tikbit.ai'}}}); refs.push(file);}
 json(path.join(home,'.tikbit/gpt-image/workstation.json'),{settings:refs}); assert.throws(()=>resolveCredentials({}, {}, {home}),/多个/);
});
test('JSON errors never echo potentially sensitive file contents', t=>{
 const home=sandbox(t), file=path.join(home,'.tikbit/gpt-image/config.json'); fs.mkdirSync(path.dirname(file),{recursive:true}); fs.writeFileSync(file,'synthetic-private-token');
 assert.throws(()=>loadConfig({home,env:{}}),e=>!e.message.includes('synthetic-private-token'));
});
test('registered vault discovery works for both Windows and macOS layouts', t=>{
 const {discover}=require('./install.cjs'); const home=sandbox(t), vault=path.join(home,'vault'); fs.mkdirSync(vault);
 for (const [platform,profile] of [['win32',path.join(home,'AppData/Roaming')],['darwin',path.join(home,'Library/Application Support')]]) {json(path.join(profile,'obsidian/obsidian.json'),{vaults:{one:{path:vault}}}); assert.deepEqual(discover(home,platform,profile),[vault]);}
});

test('synthetic CLI generation exercises request and image save without network', t=>{
 const home=sandbox(t); install({home});
 const preload=path.join(home,'synthetic-fetch.cjs'), output=path.join(home,'deliverable','sample.png');
 fs.writeFileSync(preload, `global.fetch=async (url,options)=>{if(url!=='https://example.invalid/v1/images/generations')throw new Error('Unexpected endpoint');const body=JSON.parse(options.body);if(body.model!=='gpt-image-2.5-sunburst'||body.prompt!=='synthetic test')throw new Error('Unexpected request');return new Response(JSON.stringify({data:[{b64_json:Buffer.from('synthetic-image-bytes').toString('base64')}]}),{status:200,headers:{'content-type':'application/json'}});};`);
 const result=spawnSync(process.execPath,['--require',preload,path.join(home,'.tikbit/gpt-image/gpt-image.js'),'synthetic test','--output',output],{encoding:'utf8',env:{...process.env,USERPROFILE:home,HOME:home,GPT_API_KEY:'synthetic-e2e',GPT_BASE_URL:'https://example.invalid/v1',GPT_IMAGE_MODEL:''}});
 assert.equal(result.status,0,result.stderr); assert.equal(fs.readFileSync(output,'utf8'),'synthetic-image-bytes');
});
