const { spawn } = require('child_process');
const path = require('path');

/**
 * Programmatically run agent-watch on a video URL or local file path.
 * 
 * @param {string} source - Video URL or local file path
 * @param {Object} options - CLI options
 * @returns {Promise<string>} Markdown or JSON output from agent-watch
 */
function watchVideo(source, options = {}) {
  return new Promise((resolve, reject) => {
    const watchScript = path.join(__dirname, '..', 'skills', 'watch', 'scripts', 'watch.py');
    const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
    
    const args = [watchScript, source];
    if (options.agentic) args.push('--agentic');
    if (options.ocr) args.push('--ocr');
    if (options.diarize) args.push('--diarize');
    if (options.chapters) args.push('--chapters');
    if (options.index) args.push('--index');
    if (options.serve) args.push('--serve');
    if (options.detail) args.push('--detail', options.detail);

    let stdoutData = '';
    let stderrData = '';

    const proc = spawn(pythonExecutable, args);

    proc.stdout.on('data', (data) => { stdoutData += data.toString(); });
    proc.stderr.on('data', (data) => { stderrData += data.toString(); });

    proc.on('close', (code) => {
      if (code === 0) {
        resolve(stdoutData);
      } else {
        reject(new Error(`agent-watch exited with code ${code}: ${stderrData}`));
      }
    });

    proc.on('error', (err) => {
      reject(err);
    });
  });
}

module.exports = {
  watchVideo
};
