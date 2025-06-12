use std::path::PathBuf;
use tokio::fs;
use serde_json;
use crate::media_file::MediaFile;
use crate::error::{MediaManagerError, Result};
use crate::undo::RenameOperation;

#[derive(Debug, Clone)]
pub struct RenamePreview {
    pub original_path: PathBuf,
    pub new_path: PathBuf,
    pub is_valid: bool,
    pub validation_message: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct StagedRename {
    pub original_path: PathBuf,
    pub new_path: PathBuf,
}

pub struct MediaRenamer {
    staged_renames_path: PathBuf,
}

impl MediaRenamer {
    pub fn new() -> Result<Self> {
        let mut staged_renames_path = std::env::temp_dir();
        staged_renames_path.push("media_manager_staged_renames.json");
        Ok(MediaRenamer { staged_renames_path })
    }

    /// Loads staged renames from the temporary file
    pub async fn load_staged_renames(&self) -> Result<Vec<StagedRename>> {
        if !self.staged_renames_path.exists() {
            return Ok(Vec::new());
        }
        let json_data = fs::read_to_string(&self.staged_renames_path).await?;
        let staged_renames: Vec<StagedRename> = serde_json::from_str(&json_data)?;
        Ok(staged_renames)
    }

    /// Saves staged renames to the temporary file
    pub async fn save_staged_renames(&self, staged_renames: &[StagedRename]) -> Result<()> {
        let json_data = serde_json::to_string_pretty(staged_renames)?;
        fs::write(&self.staged_renames_path, json_data).await?;
        Ok(())
    }

    /// Clears staged renames by deleting the temporary file
    pub async fn clear_staged_renames(&self) -> Result<()> {
        if self.staged_renames_path.exists() {
            fs::remove_file(&self.staged_renames_path).await?;
        }
        Ok(())
    }

    /// Generates a new filename based on a template and media file metadata.
    /// Example template: "{filename} [{resolution}]"
    pub fn apply_template(&self, media_file: &MediaFile, template: &str) -> Result<String> {
        let mut new_name = template.to_string();

        // Replace basic placeholders
        new_name = new_name.replace("{filename}", &media_file.filename);
        new_name = new_name.replace("{extension}", &media_file.extension);

        // Replace metadata placeholders if metadata is available
        if let Some(metadata) = &media_file.metadata {
            if let Some(width) = metadata.width {
                if let Some(height) = metadata.height {
                    new_name = new_name.replace("{resolution}", &format!("{}x{}", width, height));
                }
            }
            if let Some(duration) = metadata.duration_seconds {
                new_name = new_name.replace("{duration_s}", &format!("{:.0}", duration));
                // Add more duration formats (e.g., HH:MM:SS)
            }
            if let Some(codec) = &metadata.codec_name {
                new_name = new_name.replace("{codec}", codec);
            }
        }

        // Ensure the new name doesn't contain invalid characters for Windows paths
        // This is a simplified example, a more robust solution would be needed.
        let invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*'];
        if new_name.chars().any(|c| invalid_chars.contains(&c)) {
            return Err(MediaManagerError::InvalidTemplate(format!(
                "Generated filename contains invalid characters: {}",
                new_name
            )));
        }

        Ok(new_name)
    }

    /// Stages a single rename operation.
    /// This function generates the `StagedRename` struct and saves it to the temporary file.
    /// Previews a rename operation without staging it
    pub fn preview_rename(&self, media_file: &MediaFile, template: &str) -> Result<RenamePreview> {
        let new_filename_stem = match self.apply_template(media_file, template) {
            Ok(name) => name,
            Err(e) => return Ok(RenamePreview {
                original_path: media_file.path.clone(),
                new_path: media_file.path.clone(),
                is_valid: false,
                validation_message: Some(e.to_string()),
            }),
        };

        let new_filename = format!("{}.{}", new_filename_stem, media_file.extension);
        let original_dir = media_file.path.parent().ok_or_else(|| {
            MediaManagerError::Unknown(format!("Could not get parent directory for {}", media_file.path.display()))
        })?;
        let new_path = original_dir.join(&new_filename);

        // Check if target path already exists
        let is_valid = !new_path.exists();
        let validation_message = if !is_valid {
            Some("Target path already exists".to_string())
        } else {
            None
        };

        Ok(RenamePreview {
            original_path: media_file.path.clone(),
            new_path,
            is_valid,
            validation_message,
        })
    }

    pub async fn stage_single_rename(&self, media_file: &MediaFile, template: &str) -> Result<()> {
        let new_filename_stem = self.apply_template(media_file, template)?;
        let new_filename = format!("{}.{}", new_filename_stem, media_file.extension);

        let original_dir = media_file.path.parent().ok_or_else(|| {
            MediaManagerError::Unknown(format!("Could not get parent directory for {}", media_file.path.display()))
        })?;
        let new_path = original_dir.join(&new_filename);

        let staged_rename = StagedRename {
            original_path: media_file.path.clone(),
            new_path,
        };

        let mut staged_renames = self.load_staged_renames().await?;
        staged_renames.push(staged_rename);
        self.save_staged_renames(&staged_renames).await?;

        Ok(())
    }

    /// Applies a batch of staged renames.
    /// Returns a vector of `RenameOperation` for undo purposes.
    pub async fn commit_renames(&self) -> Result<Vec<RenameOperation>> {
        let staged_renames = self.load_staged_renames().await?;
        if staged_renames.is_empty() {
            return Err(MediaManagerError::NoStagedRenames);
        }

        let mut committed_operations = Vec::new();

        for staged_rename in staged_renames {
            log::info!(
                "Attempting to rename '{}' to '{}'",
                staged_rename.original_path.display(),
                staged_rename.new_path.display()
            );
            match fs::rename(&staged_rename.original_path, &staged_rename.new_path).await {
                Ok(_) => {
                    log::info!("Successfully renamed.");
                    committed_operations.push(RenameOperation {
                        original_path: staged_rename.original_path,
                        new_path: staged_rename.new_path,
                    });
                }
                Err(e) => {
                    log::error!(
                        "Failed to rename '{}' to '{}': {}",
                        staged_rename.original_path.display(),
                        staged_rename.new_path.display(),
                        e
                    );
                    // Decide whether to stop on first error or continue
                    return Err(MediaManagerError::RenameFailed(
                        staged_rename.original_path,
                        staged_rename.new_path,
                        e.to_string(),
                    ));
                }
            }
        }

        // Clear staged renames after successful commit
        self.clear_staged_renames().await?;
        Ok(committed_operations)
    }

    /// Reverts a batch of rename operations.
    pub async fn undo_renames(&self, operations: Vec<RenameOperation>) -> Result<()> {
        if operations.is_empty() {
            return Err(MediaManagerError::NoUndoData);
        }

        // Undo in reverse order of commitment for safety (if dependencies exist)
        for op in operations.into_iter().rev() {
            log::info!(
                "Attempting to undo rename: '{}' back to '{}'",
                op.new_path.display(),
                op.original_path.display()
            );
            match fs::rename(&op.new_path, &op.original_path).await {
                Ok(_) => {
                    log::info!("Successfully undone.");
                }
                Err(e) => {
                    log::error!(
                        "Failed to undo rename '{}' back to '{}': {}",
                        op.new_path.display(),
                        op.original_path.display(),
                        e
                    );
                    // Decide whether to stop on first error or continue
                    return Err(MediaManagerError::RenameFailed(
                        op.new_path,
                        op.original_path,
                        e.to_string(),
                    ));
                }
            }
        }
        Ok(())
    }
}
