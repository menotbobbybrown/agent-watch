#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

const scriptsDir = path.join(__dirname, '..', 'skills', 'watch', 'scripts');
const watchScript = path.join(scriptsDir, 'watch.py');
const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
const args = [watchScript, ...process.argv.slice(2)];

const env = { 
  ...process.env, 
  PYTHONPATH: scriptsDir + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : '') 
};

const proc = spawn(pythonExecutable, args, { stdio: 'inherit', env });

proc.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.error(`[agent-watch] Error: Python executable '${pythonExecutable}' not found. Please install Python 3.9+`);
  } else {
    console.error(`[agent-watch] Execution error: ${err.message}`);
  }
  process.exit(1);
});

proc.on('close', (code) => {
  process.exit(code || 0);
});
