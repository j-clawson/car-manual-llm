// Script to run TypeScript compiler in watch mode
const { spawn } = require('child_process');
const path = require('path');

// Path to local TypeScript compiler
const tscPath = path.join(__dirname, 'node_modules', '.bin', 'tsc');

// Print Node.js version
console.log('Using Node.js version:', process.version);
console.log('Starting TypeScript compiler in watch mode...');

// Run tsc command with --watch flag
const tscProcess = spawn(tscPath, ['--watch'], { 
  stdio: 'inherit',
  shell: true 
});

// Handle process exit
tscProcess.on('close', (code) => {
  if (code !== 0) {
    console.error(`TypeScript compiler exited with code ${code}`);
  }
});

console.log('Press Ctrl+C to stop watching...'); 