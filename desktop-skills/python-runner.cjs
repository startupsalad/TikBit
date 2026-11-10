'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const home = os.homedir();
const runtime = path.join(home, '.tikbit/tool-runtime/runtime.json');
const config = fs.existsSync(runtime) ? JSON.parse(fs.readFileSync(runtime, 'utf8')) : {};
const script = path.resolve(__dirname, process.argv[2] || '');
const relative = path.relative(__dirname, script);
if (!relative || relative.startsWith('..') || path.isAbsolute(relative) || !fs.statSync(script).isFile()) process.exit(2);
const python = typeof config.python === 'string' ? config.python : process.platform === 'win32' ? 'python' : 'python3';
const site = path.join(home, '.tikbit/tool-runtime/python-packages');
const result = spawnSync(python, [script, ...process.argv.slice(3)], { windowsHide: true, stdio: 'inherit',
  env: { ...process.env, PYTHONUTF8: '1', PYTHONPATH: [site, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter) } });
process.exit(result.status ?? 1);
