const fs = require('fs');
const path = require('path');

console.log('Verifying build output...\n');

const requiredFiles = [
  { path: 'dist/main.js', description: 'Main process bundle' },
  { path: 'dist/preload.js', description: 'Preload script' },
  { path: 'dist/renderer/index.html', description: 'Renderer HTML file' },
  { path: 'dist/renderer/main.js', description: 'Renderer JavaScript bundle' },
  { path: 'target/release/media_manager_cli.exe', description: 'Rust CLI executable' }
];

let allFilesExist = true;
const missingFiles = [];

// Check each required file
requiredFiles.forEach(file => {
  const fullPath = path.join(process.cwd(), file.path);
  const exists = fs.existsSync(fullPath);
  
  console.log(`${exists ? '✓' : '✗'} ${file.description}`);
  console.log(`  Path: ${file.path}`);
  
  if (exists) {
    const stats = fs.statSync(fullPath);
    console.log(`  Size: ${(stats.size / 1024).toFixed(2)} KB`);
    console.log(`  Modified: ${stats.mtime.toLocaleString()}`);
  } else {
    allFilesExist = false;
    missingFiles.push(file);
  }
  
  console.log('');
});

// Check directory structure
console.log('Directory Structure:');
console.log('dist/');
if (fs.existsSync('dist')) {
  const distContents = fs.readdirSync('dist');
  distContents.forEach(item => {
    console.log(`  - ${item}`);
    if (item === 'renderer' && fs.existsSync('dist/renderer')) {
      const rendererContents = fs.readdirSync('dist/renderer');
      rendererContents.forEach(subItem => {
        console.log(`    - ${subItem}`);
      });
    }
  });
} else {
  console.log('  [Directory not found]');
}

console.log('\n' + '='.repeat(50) + '\n');

if (allFilesExist) {
  console.log('✓ Build verification PASSED - All required files exist');
  process.exit(0);
} else {
  console.log('✗ Build verification FAILED - Missing files:');
  missingFiles.forEach(file => {
    console.log(`  - ${file.description} (${file.path})`);
  });
  
  console.log('\nPossible solutions:');
  console.log('1. Run "npm run build" to build the Electron app');
  console.log('2. Run "cargo build --release" to build the Rust CLI');
  console.log('3. Check webpack configuration for correct output paths');
  
  process.exit(1);
}
