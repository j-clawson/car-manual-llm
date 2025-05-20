// Simple script to compile TypeScript files
const { execSync } = require('child_process');
const path = require('path');

// Path to local TypeScript compiler
const tscPath = path.join(__dirname, 'node_modules', '.bin', 'tsc');

try {
  // Print Node.js version
  console.log('Using Node.js version:', process.version);
  
  // Run tsc command to compile TypeScript
  const output = execSync(`${tscPath}`, { encoding: 'utf8' });
  console.log('TypeScript compilation successful!');
  
  if (output) {
    console.log(output);
  }
} catch (error) {
  console.error('Error compiling TypeScript:', error.message);
  process.exit(1);
} 