'use strict';
const fs = require('fs');
const os = require('os');
const { createHash } = require('crypto');
const path = require('path');
const { spawnSync } = require('child_process');
const args = process.argv.slice(2);
const mode = args[0] || 'done';
if (!['done', 'stuck', 'ask', 'perm', 'error', 'wait'].includes(mode)) process.exit(2);
const vault = process.cwd();
const normalized = process.platform === 'win32' ? path.resolve(vault).toLowerCase() : path.resolve(vault);
const id = createHash('sha256').update(normalized).digest('hex');
const contextFile = path.join(os.homedir(), '.tikbit/tool-runtime/contexts', id + '.json');
const context = fs.existsSync(contextFile) ? JSON.parse(fs.readFileSync(contextFile, 'utf8')) : {};
const config = args[1] && !args[1].startsWith('--') ? args[1] : context.configDir;
if (typeof config !== 'string') process.exit(2);
if (!/^\.[^\\/:\x00-\x1f]+$/.test(config) || config === '..') process.exit(2);
const engine = path.join(__dirname, 'resources', 'engine');
const env = { ...process.env, TIKBIT_VAULT_ROOT: vault, TIKBIT_OBSIDIAN_CONFIG_DIR: config };
if (env.TIKBIT_VOICE_SUPPRESS === '1') process.exit(0);
const dry = args.includes('--dry-run');
const command = process.platform === 'win32' ? 'powershell.exe' : '/bin/bash';
const params = process.platform === 'win32'
  ? ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(engine, 'notify-voice.ps1'), '-Mode', mode, ...(dry ? ['-DryRun'] : [])]
  : [path.join(engine, 'notify-voice.sh'), mode, ...(dry ? ['--dry-run'] : [])];
if (!fs.existsSync(params[process.platform === 'win32' ? 4 : 0])) process.exit(2);
const result = spawnSync(command, params, { cwd: vault, env, windowsHide: true, stdio: 'inherit', timeout: 20000 });
process.exit(result.status ?? 1);
