#!/usr/bin/env node

// Watch script that doesn't depend on TypeScript's watch mode
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Log which Node.js is being used
console.log('Node.js path:', process.execPath);
console.log('Node.js version:', process.version);

// Path to the build script
const buildScript = path.join(__dirname, 'build-ts.js');

// TypeScript directory to watch
const tsDir = path.join(__dirname, 'static', 'ts');
const tsFilePath = path.join(tsDir, 'script.ts');

console.log(`Watching for changes in: ${tsFilePath}`);
console.log('Press Ctrl+C to stop watching.');

// Run initial build
console.log('Running initial build...');
runBuild();

// Watch for changes
fs.watchFile(tsFilePath, { interval: 1000 }, (curr, prev) => {
  if (curr.mtime !== prev.mtime) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] Changes detected in script.ts`);
    console.log('Rebuilding...');
    runBuild();
  }
});

function runBuild() {
  const buildProcess = spawn('node', ['build-ts.js'], {
    stdio: 'inherit'
  });

  buildProcess.on('close', (code) => {
    if (code === 0) {
      console.log('Rebuild complete!');
    } else {
      console.error(`TypeScript compilation failed with code ${code}`);
    }
  });
} 