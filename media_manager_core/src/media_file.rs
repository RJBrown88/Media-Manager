use std::path::PathBuf;
use crate::metadata::MediaMetadata;

#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum MediaFileType {
    Video,
    Audio,
    // Add other types as needed
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct MediaFile {
    pub path: PathBuf,
    pub filename: String, // e.g., "my_movie"
    pub extension: String, // e.g., "mp4"
    pub file_type: MediaFileType,
    pub metadata: Option<MediaMetadata>, // Option because ffprobe might fail or not be run
}

impl MediaFile {
    /// Creates a new MediaFile from a path.
    /// Attempts to determine filename, extension, and basic file type.
    pub fn new(path: PathBuf) -> Self {
        let filename = path.file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .to_string();
        let extension = path.extension()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .to_string();

        let file_type = match extension.to_lowercase().as_str() {
            "mp4" | "mkv" | "avi" | "mov" | "webm" => MediaFileType::Video,
            // Add more extensions for audio, images, etc.
            _ => MediaFileType::Video, // Default for now, refine later
        };

        MediaFile {
            path,
            filename,
            extension,
            file_type,
            metadata: None,
        }
    }

    /// Returns the full file name including extension.
    pub fn full_filename(&self) -> String {
        format!("{}.{}", self.filename, self.extension)
    }
}
