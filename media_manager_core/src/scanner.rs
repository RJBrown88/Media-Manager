use std::path::Path;
use tokio::fs;
use async_recursion::async_recursion; // For recursive async functions
use crate::media_file::MediaFile;
use crate::metadata::MediaMetadata;
use crate::error::Result;

pub struct MediaScanner {
    // Configurable allowed extensions
    allowed_extensions: Vec<String>,
}

impl MediaScanner {
    pub fn new() -> Self {
        MediaScanner {
            allowed_extensions: vec![
                "mp4".to_string(),
                "mkv".to_string(),
                "avi".to_string(),
                "mov".to_string(),
                "webm".to_string(),
            ],
        }
    }

    /// Recursively scans a directory for media files.
    #[async_recursion]
    pub async fn scan_directory(&self, path: &Path) -> Result<Vec<MediaFile>> {
        let mut media_files = Vec::new();
        let mut entries = fs::read_dir(path).await?;

        while let Some(entry) = entries.next_entry().await? {
            let entry_path = entry.path();
            if entry_path.is_dir() {
                // Recursively scan subdirectories
                media_files.extend(self.scan_directory(&entry_path).await?);
            } else if entry_path.is_file() {
                if let Some(ext) = entry_path.extension().and_then(|s| s.to_str()) {
                    if self.allowed_extensions.contains(&ext.to_lowercase()) {
                        let mut media_file = MediaFile::new(entry_path);
                        // Attempt to get metadata, but don't fail if it doesn't work
                        match MediaMetadata::from_file(&media_file.path).await {
                            Ok(metadata) => media_file.metadata = Some(metadata),
                            Err(e) => {
                                log::warn!("Could not get metadata for {}: {}", media_file.path.display(), e);
                                // Continue without metadata
                            }
                        }
                        media_files.push(media_file);
                    }
                }
            }
        }
        Ok(media_files)
    }
}
