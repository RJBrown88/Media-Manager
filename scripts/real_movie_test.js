#!/usr/bin/env node

/**
 * Real movie file test script
 * Tests the media manager with actual movie files from network paths
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
    cyan: '\x1b[36m',
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

async function testWithRealMovies() {
    log('\n🎬 Testing Media Manager with Real Movie Files', colors.blue);
    log('===============================================', colors.blue);
    
    const movieDirectories = [
        '\\\\Plex\\e\\movies\\Star Wars Episode I - The Phantom Menace (1999)',
        '\\\\Plex\\e\\movies\\28 Weeks Later (2007) {tmdb-1562}'
    ];
    
    const results = {
        ffprobe: false,
        status: false,
        scan: false,
        metadata: false,
        subtitles: false
    };
    
    // Step 1: Check FFprobe availability
    log('\n🔍 Step 1: Checking FFprobe availability...', colors.blue);
    try {
        await runCommand('ffprobe', ['-version']);
        log('✅ FFprobe is available', colors.green);
        results.ffprobe = true;
    } catch (error) {
        log('❌ FFprobe not found', colors.red);
        log('   Please install FFmpeg to enable media file analysis', colors.yellow);
        return results;
    }
    
    // Step 2: Test CLI status
    log('\n🔍 Step 2: Testing CLI status...', colors.blue);
    try {
        const result = await runCommand('cargo', ['run', '--bin', 'media_manager_cli', '--', 'status']);
        const status = JSON.parse(result.stdout);
        
        log('✅ CLI status command works', colors.green);
        log(`   Version: ${status.version}`, colors.green);
        log(`   Platform: ${status.platform}`, colors.green);
        log(`   FFprobe: ${status.ffprobe}`, colors.green);
        
        results.status = true;
    } catch (error) {
        log('❌ CLI status command failed', colors.red);
        log(`   Error: ${error.error || error.stderr}`, colors.red);
        return results;
    }
    
    // Step 3: Test with real movie directories
    log('\n🔍 Step 3: Testing with real movie directories...', colors.blue);
    
    for (const movieDir of movieDirectories) {
        log(`\n🎬 Testing directory: ${movieDir}`, colors.cyan);
        
        // Check if directory exists
        if (!fs.existsSync(movieDir)) {
            log(`❌ Directory not found: ${movieDir}`, colors.red);
            log(`   This might be a network path issue or the path might be incorrect`, colors.yellow);
            continue;
        }
        
        log(`✅ Directory exists`, colors.green);
        
        try {
            log(`🔍 Scanning directory...`, colors.cyan);
            
            const result = await runCommand('cargo', ['run', '--bin', 'media_manager_cli', '--', 'scan', `"${movieDir}"`]);
            const scanResult = JSON.parse(result.stdout);
            
            log(`✅ Scan successful`, colors.green);
            log(`   Found ${scanResult.count} files`, colors.green);
            
            if (scanResult.files.length > 0) {
                results.scan = true;
                
                log(`\n📋 File Details:`, colors.cyan);
                
                scanResult.files.forEach((file, index) => {
                    const fileName = path.basename(file.path);
                    log(`   ${index + 1}. ${fileName}`, colors.cyan);
                    log(`      Resolution: ${file.metadata.resolution}`, colors.cyan);
                    log(`      Duration: ${file.metadata.duration}`, colors.cyan);
                    log(`      Codec: ${file.metadata.codec}`, colors.cyan);
                    log(`      Subtitle streams: ${file.metadata.subtitle_streams.length}`, colors.cyan);
                    
                    // Check if we got real metadata (not "N/A")
                    if (file.metadata.resolution !== "N/A") {
                        results.metadata = true;
                        log(`      ✅ Real metadata extracted`, colors.green);
                    } else {
                        log(`      ⚠️  No metadata extracted (file might not be accessible)`, colors.yellow);
                    }
                    
                    // Check subtitle streams
                    if (file.metadata.subtitle_streams.length > 0) {
                        results.subtitles = true;
                        log(`      ✅ Subtitle streams detected:`, colors.green);
                        file.metadata.subtitle_streams.forEach((stream, streamIndex) => {
                            log(`         - Track ${stream.index}: ${stream.language || 'Unknown'} (${stream.codec})`, colors.green);
                        });
                    } else {
                        log(`      ℹ️  No subtitle streams found`, colors.cyan);
                    }
                });
            } else {
                log(`⚠️  No media files found in directory`, colors.yellow);
            }
            
        } catch (error) {
            log(`❌ Scan failed for ${movieDir}`, colors.red);
            log(`   Error: ${error.error || error.stderr}`, colors.red);
        }
    }
    
    // Summary
    log('\n📊 Test Results Summary', colors.blue);
    log('======================', colors.blue);
    log(`FFprobe Available: ${results.ffprobe ? '✅ PASS' : '❌ FAIL'}`, results.ffprobe ? colors.green : colors.red);
    log(`CLI Status: ${results.status ? '✅ PASS' : '❌ FAIL'}`, results.status ? colors.green : colors.red);
    log(`Directory Scanning: ${results.scan ? '✅ PASS' : '❌ FAIL'}`, results.scan ? colors.green : colors.red);
    log(`Metadata Extraction: ${results.metadata ? '✅ PASS' : '❌ FAIL'}`, results.metadata ? colors.green : colors.red);
    log(`Subtitle Detection: ${results.subtitles ? '✅ PASS' : '❌ FAIL'}`, results.subtitles ? colors.green : colors.red);
    
    const allPassed = results.ffprobe && results.status && results.scan && results.metadata;
    
    if (allPassed) {
        log('\n🎉 SUCCESS! Your media manager is fully functional with real files!', colors.green);
        log('   You can now use the GUI to scan and manage your media files.', colors.green);
    } else {
        log('\n⚠️  Some tests failed. Here are the issues:', colors.yellow);
        
        if (!results.ffprobe) {
            log('   - Install FFmpeg to enable media file analysis', colors.yellow);
        }
        
        if (!results.scan) {
            log('   - Check network path accessibility', colors.yellow);
        }
        
        if (!results.metadata) {
            log('   - FFprobe might not be able to access the files', colors.yellow);
        }
    }
    
    return results;
}

// Run the test
testWithRealMovies().catch(error => {
    log(`\n💥 Test failed: ${error.message}`, colors.red);
    process.exit(1);
});