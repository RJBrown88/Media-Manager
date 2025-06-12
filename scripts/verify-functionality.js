#!/usr/bin/env node

/**
 * Verification script to test end-to-end functionality
 * This script tests the core features of the media manager
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    reset: '\x1b[0m'
};

function log(message, color = '') {
    console.log(`${color}${message}${colors.reset}`);
}

function runCommand(command, args = []) {
    return new Promise((resolve, reject) => {
        const child = spawn(command, args, { 
            stdio: ['pipe', 'pipe', 'pipe'],
            shell: true 
        });
        
        let stdout = '';
        let stderr = '';
        
        child.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        child.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        child.on('close', (code) => {
            if (code === 0) {
                resolve({ stdout, stderr, code });
            } else {
                reject({ stdout, stderr, code });
            }
        });
        
        child.on('error', (error) => {
            reject({ error: error.message, code: -1 });
        });
    });
}

async function testStatusCommand() {
    log('\n🔍 Testing status command...', colors.blue);
    
    try {
        const result = await runCommand('cargo', ['run', '--bin', 'media_manager_cli', '--', 'status']);
        const status = JSON.parse(result.stdout);
        
        log('✅ Status command works', colors.green);
        log(`   Version: ${status.version}`, colors.green);
        log(`   Platform: ${status.platform}`, colors.green);
        log(`   FFprobe: ${status.ffprobe}`, colors.green);
        
        return true;
    } catch (error) {
        log('❌ Status command failed', colors.red);
        log(`   Error: ${error.error || error.stderr}`, colors.red);
        return false;
    }
}

async function testScanCommand() {
    log('\n🔍 Testing scan command...', colors.blue);
    
    // Create a temporary test directory
    const testDir = path.join(__dirname, '..', 'test_scan');
    if (!fs.existsSync(testDir)) {
        fs.mkdirSync(testDir, { recursive: true });
    }
    
    // Create a mock video file
    const testFile = path.join(testDir, 'test_video.mp4');
    fs.writeFileSync(testFile, 'mock video content');
    
    try {
        const result = await runCommand('cargo', ['run', '--bin', 'media_manager_cli', '--', 'scan', testDir]);
        const scanResult = JSON.parse(result.stdout);
        
        log('✅ Scan command works', colors.green);
        log(`   Found ${scanResult.count} files`, colors.green);
        log(`   Directory: ${scanResult.directory}`, colors.green);
        
        if (scanResult.files.length > 0) {
            const file = scanResult.files[0];
            log(`   File: ${file.path}`, colors.green);
            log(`   Resolution: ${file.metadata.resolution}`, colors.green);
            log(`   Duration: ${file.metadata.duration}`, colors.green);
            log(`   Codec: ${file.metadata.codec}`, colors.green);
            log(`   Subtitle streams: ${file.metadata.subtitle_streams.length}`, colors.green);
        }
        
        // Clean up
        fs.rmSync(testDir, { recursive: true, force: true });
        
        return true;
    } catch (error) {
        log('❌ Scan command failed', colors.red);
        log(`   Error: ${error.error || error.stderr}`, colors.red);
        
        // Clean up on error
        if (fs.existsSync(testDir)) {
            fs.rmSync(testDir, { recursive: true, force: true });
        }
        
        return false;
    }
}

async function testBuildSystem() {
    log('\n🔍 Testing build system...', colors.blue);
    
    try {
        // Test Rust build
        await runCommand('cargo', ['build', '--release']);
        log('✅ Rust build successful', colors.green);
        
        // Test if CLI executable exists
        const cliPath = path.join(__dirname, '..', 'target', 'release', 'media_manager_cli.exe');
        if (fs.existsSync(cliPath)) {
            log('✅ CLI executable exists', colors.green);
        } else {
            log('❌ CLI executable not found', colors.red);
            return false;
        }
        
        return true;
    } catch (error) {
        log('❌ Build failed', colors.red);
        log(`   Error: ${error.error || error.stderr}`, colors.red);
        return false;
    }
}

async function main() {
    log('🚀 Media Manager Functionality Verification', colors.blue);
    log('============================================', colors.blue);
    
    const results = {
        build: false,
        status: false,
        scan: false
    };
    
    // Test build system
    results.build = await testBuildSystem();
    
    if (results.build) {
        // Test status command
        results.status = await testStatusCommand();
        
        // Test scan command
        results.scan = await testScanCommand();
    }
    
    // Summary
    log('\n📊 Test Results Summary', colors.blue);
    log('======================', colors.blue);
    log(`Build System: ${results.build ? '✅ PASS' : '❌ FAIL'}`, results.build ? colors.green : colors.red);
    log(`Status Command: ${results.status ? '✅ PASS' : '❌ FAIL'}`, results.status ? colors.green : colors.red);
    log(`Scan Command: ${results.scan ? '✅ PASS' : '❌ FAIL'}`, results.scan ? colors.green : colors.red);
    
    const allPassed = results.build && results.status && results.scan;
    
    if (allPassed) {
        log('\n🎉 All tests passed! The media manager is working correctly.', colors.green);
        process.exit(0);
    } else {
        log('\n⚠️  Some tests failed. Please check the errors above.', colors.yellow);
        process.exit(1);
    }
}

// Run the verification
main().catch(error => {
    log(`\n💥 Verification script failed: ${error.message}`, colors.red);
    process.exit(1);
}); 