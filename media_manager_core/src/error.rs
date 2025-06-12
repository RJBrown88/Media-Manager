use thiserror::Error;
use std::path::PathBuf;
use crate::subtitles::SubtitleError;

#[derive(Error, Debug)]
pub enum MediaManagerError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON parsing error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("ffprobe command failed: {0}")]
    FfprobeError(String),
    #[error("ffprobe not found. Please ensure it's installed and in your PATH.")]
    FfprobeNotFound,
    #[error("File not found: {0}")]
    FileNotFound(PathBuf),
    #[error("Invalid template: {0}")]
    InvalidTemplate(String),
    #[error("Rename failed for '{0}' to '{1}': {2}")]
    RenameFailed(PathBuf, PathBuf, String),
    #[error("No staged renames to commit.")]
    NoStagedRenames,
    #[error("No previous rename batch to undo.")]
    NoUndoData,
    #[error("Operation cancelled.")]
    Cancelled,
    #[error("Unknown error: {0}")]
    Unknown(String),
    #[error("Subtitle error: {0}")]
    Subtitle(#[from] SubtitleError),
}

pub type Result<T> = std::result::Result<T, MediaManagerError>;
