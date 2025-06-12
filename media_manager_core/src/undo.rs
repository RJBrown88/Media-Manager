use std::path::PathBuf;
use tokio::fs;
use serde::{Deserialize, Serialize};
use crate::error::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RenameOperation {
    pub original_path: PathBuf,
    pub new_path: PathBuf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UndoData {
    pub operations: Vec<RenameOperation>,
}

pub struct UndoManager {
    undo_file_path: PathBuf,
}

impl UndoManager {
    pub fn new() -> Result<Self> {
        // Create a .media_manager directory in the current directory
        let mut undo_dir = std::env::current_dir()?;
        undo_dir.push(".media_manager");
        if !undo_dir.exists() {
            std::fs::create_dir(&undo_dir)?;
        }
        
        let mut undo_file_path = undo_dir;
        undo_file_path.push("undo_data.json");
        
        Ok(UndoManager { undo_file_path })
    }

    /// Saves the current batch of rename operations for undo.
    pub async fn save_undo_data(&self, data: &UndoData) -> Result<()> {
        let json_data = serde_json::to_string_pretty(data)?;
        fs::write(&self.undo_file_path, json_data).await?;
        log::info!("Undo data saved to: {}", self.undo_file_path.display());
        Ok(())
    }

    /// Loads the last saved undo data.
    pub async fn load_undo_data(&self) -> Result<Option<UndoData>> {
        if !self.undo_file_path.exists() {
            return Ok(None);
        }
        let json_data = fs::read_to_string(&self.undo_file_path).await?;
        let data: UndoData = serde_json::from_str(&json_data)?;
        log::info!("Undo data loaded from: {}", self.undo_file_path.display());
        Ok(Some(data))
    }

    /// Clears the undo data.
    pub async fn clear_undo_data(&self) -> Result<()> {
        if self.undo_file_path.exists() {
            fs::remove_file(&self.undo_file_path).await?;
            log::info!("Undo data cleared.");
        }
        Ok(())
    }
}
