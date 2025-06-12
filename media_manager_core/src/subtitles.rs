use std::path::Path;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum SubtitleError {
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    #[error("No subtitles found")]
    NoSubtitlesFound,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SubtitleMetadata {
    pub language: String,
    pub codec: String,
}

/// A simplified subtitle manager that works with embedded subtitle streams
/// detected during the scan phase. This replaces the previous API-dependent implementation.
#[derive(Debug)]
pub struct SubtitleManager;

impl SubtitleManager {
    /// Creates a new SubtitleManager instance
    pub async fn new() -> Result<Self, SubtitleError> {
        // No API key needed in simplified version
        Ok(Self {})
    }

    /// Returns information about embedded subtitle streams in a video file
    /// This is a placeholder as the actual subtitle detection happens in metadata.rs
    pub async fn get_embedded_subtitles(&self, _video_path: &Path) -> Result<Vec<SubtitleMetadata>, SubtitleError> {
        // This is just a placeholder - the actual subtitle detection happens during scan
        // in the MediaMetadata::from_file method
        Ok(Vec::new())
    }

    /// Extracts IMDB ID from a filename if present (simplified version)
    pub fn extract_imdb_id(filename: &str) -> Option<String> {
        // Simple string-based IMDB ID extraction (e.g., "Movie.Title.tt1234567.mkv")
        if filename.contains("tt") {
            let parts: Vec<&str> = filename.split("tt").collect();
            if parts.len() > 1 {
                let after_tt = parts[1];
                if after_tt.len() >= 7 {
                    let id_part = &after_tt[..7];
                    if id_part.chars().all(|c| c.is_digit(10)) {
                        return Some(format!("tt{}", id_part));
                    }
                }
            }
        }
        None
    }

    /// Generates an OpenSubtitles search URL for a video file (simplified)
    pub fn get_opensubtitles_url(video_path: &Path) -> String {
        let filename = video_path.file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("");
            
        if let Some(imdb_id) = Self::extract_imdb_id(filename) {
            format!("https://www.opensubtitles.org/en/search/sublanguageid-all/imdbid-{}", imdb_id)
        } else {
            let movie_name = video_path.file_stem()
                .and_then(|n| n.to_str())
                .unwrap_or(filename);
            // Simple URL encoding - replace spaces with %20
            let encoded_name = movie_name.replace(" ", "%20");
            format!("https://www.opensubtitles.org/en/search/sublanguageid-all/moviename-{}", encoded_name)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_extract_imdb_id() {
        assert_eq!(SubtitleManager::extract_imdb_id("Movie.Title.tt1234567.mkv"), Some("tt1234567".to_string()));
        assert_eq!(SubtitleManager::extract_imdb_id("tt9999999_movie.mp4"), Some("tt9999999".to_string()));
        assert_eq!(SubtitleManager::extract_imdb_id("movie_without_id.mp4"), None);
    }

    #[test]
    fn test_get_opensubtitles_url() {
        let path1 = PathBuf::from("Movie.Title.tt1234567.mkv");
        assert_eq!(
            SubtitleManager::get_opensubtitles_url(&path1),
            "https://www.opensubtitles.org/en/search/sublanguageid-all/imdbid-tt1234567"
        );

        let path2 = PathBuf::from("movie_without_id.mp4");
        assert_eq!(
            SubtitleManager::get_opensubtitles_url(&path2),
            "https://www.opensubtitles.org/en/search/sublanguageid-all/moviename-movie_without_id"
        );
    }
}
