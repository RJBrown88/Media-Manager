use assert_cmd::Command;
use predicates::prelude::*;
use serde_json::Value;
use std::fs;
use std::path::PathBuf;

#[tokio::test]
async fn test_status_command_basic() {
    let mut cmd = Command::cargo_bin("media_manager_cli").unwrap();
    let assert = cmd.arg("status").assert();
    
    // Should succeed and return JSON
    assert.success()
        .stdout(predicate::str::contains("version"))
        .stdout(predicate::str::contains("platform"))
        .stdout(predicate::str::contains("ffprobe"))
        .stdout(predicate::str::contains("lastOperation"));
}

#[tokio::test]
async fn test_status_command_json_format() {
    let mut cmd = Command::cargo_bin("media_manager_cli").unwrap();
    let output = cmd.arg("status").output().unwrap();
    
    let stdout = String::from_utf8(output.stdout).unwrap();
    let status: Value = serde_json::from_str(&stdout).unwrap();
    
    // Verify JSON structure
    assert!(status.get("version").is_some());
    assert!(status.get("platform").is_some());
    assert!(status.get("ffprobe").is_some());
    assert!(status.get("lastOperation").is_some());
    
    // Verify ffprobe field is either "ok" or "not_found"
    let ffprobe = status["ffprobe"].as_str().unwrap();
    assert!(ffprobe == "ok" || ffprobe == "not_found");
}

#[tokio::test]
async fn test_scan_command_json_format() {
    let mut cmd = Command::cargo_bin("media_manager_cli").unwrap();
    let output = cmd.arg("scan").arg(".").output().unwrap();
    
    let stdout = String::from_utf8(output.stdout).unwrap();
    let result: Value = serde_json::from_str(&stdout).unwrap();
    
    // Verify JSON structure
    assert!(result.get("files").is_some());
    assert!(result.get("count").is_some());
    assert!(result.get("directory").is_some());
    
    // Verify files array
    let files = result["files"].as_array().unwrap();
    let count = result["count"].as_u64().unwrap();
    assert_eq!(files.len() as u64, count);
    
    // If there are files, verify they have the expected structure
    if !files.is_empty() {
        let first_file = &files[0];
        assert!(first_file.get("path").is_some());
        assert!(first_file.get("metadata").is_some());
        
        let metadata = &first_file["metadata"];
        assert!(metadata.get("resolution").is_some());
        assert!(metadata.get("duration").is_some());
        assert!(metadata.get("codec").is_some());
        assert!(metadata.get("subtitle_streams").is_some());
    }
}

#[tokio::test]
async fn test_scan_command_empty_directory() {
    // Create a temporary empty directory
    let temp_dir = tempfile::tempdir().unwrap();
    
    let mut cmd = Command::cargo_bin("media_manager_cli").unwrap();
    let output = cmd.arg("scan").arg(temp_dir.path()).output().unwrap();
    
    let stdout = String::from_utf8(output.stdout).unwrap();
    let result: Value = serde_json::from_str(&stdout).unwrap();
    
    assert_eq!(result["count"].as_u64().unwrap(), 0);
    assert_eq!(result["files"].as_array().unwrap().len(), 0);
}

#[tokio::test]
async fn test_scan_command_with_test_files() {
    // Create a temporary directory with test files
    let temp_dir = tempfile::tempdir().unwrap();
    let test_dir = temp_dir.path().join("test_media");
    fs::create_dir(&test_dir).unwrap();
    
    // Create a mock video file (not a real video, but should be detected as a file)
    let video_path = test_dir.join("test_video.mp4");
    fs::write(&video_path, b"mock video content").unwrap();
    
    let mut cmd = Command::cargo_bin("media_manager_cli").unwrap();
    let output = cmd.arg("scan").arg(&test_dir).output().unwrap();
    
    let stdout = String::from_utf8(output.stdout).unwrap();
    let result: Value = serde_json::from_str(&stdout).unwrap();
    
    // Should find the test file
    assert_eq!(result["count"].as_u64().unwrap(), 1);
    let files = result["files"].as_array().unwrap();
    assert_eq!(files.len(), 1);
    
    // Verify the file structure
    let file = &files[0];
    assert!(file["path"].as_str().unwrap().contains("test_video.mp4"));
    
    let metadata = &file["metadata"];
    assert!(metadata.get("resolution").is_some());
    assert!(metadata.get("duration").is_some());
    assert!(metadata.get("codec").is_some());
    assert!(metadata.get("subtitle_streams").is_some());
    
    // Since it's not a real video file, metadata should be "N/A"
    assert_eq!(metadata["resolution"].as_str().unwrap(), "N/A");
    assert_eq!(metadata["duration"].as_str().unwrap(), "N/A");
    assert_eq!(metadata["codec"].as_str().unwrap(), "N/A");
    
    // Subtitle streams should be empty array
    let subtitle_streams = metadata["subtitle_streams"].as_array().unwrap();
    assert_eq!(subtitle_streams.len(), 0);
}

#[tokio::test]
async fn test_invalid_command() {
    let mut cmd = Command::cargo_bin("media_manager_cli").unwrap();
    let assert = cmd.arg("invalid-command").assert();
    
    // Should fail with non-zero exit code
    assert.failure();
}
