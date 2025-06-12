use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use directories::ProjectDirs;
use tokio::fs;
use crate::error::Result;

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    // Simplified config without API key management
}

impl Default for Config {
    fn default() -> Self {
        Self {}
    }
}

impl Config {
    pub async fn load() -> Result<Self> {
        let config_path = Self::get_config_path()?;
        
        if config_path.exists() {
            let content = fs::read_to_string(&config_path).await?;
            // Normalize line endings and whitespace before parsing
            let content = content.replace("\r\n", "\n").trim().to_string();
            Ok(serde_json::from_str(&content)?)
        } else {
            Ok(Config::default())
        }
    }

    pub async fn save(&self) -> Result<()> {
        let config_path = Self::get_config_path()?;
        
        // Ensure config directory exists
        if let Some(parent) = config_path.parent() {
            fs::create_dir_all(parent).await?;
        }
        
        // Format JSON with consistent indentation and line endings
        let mut content = serde_json::to_string_pretty(self)?;
        content = content.replace("\r\n", "\n");
        content = content.trim().to_string();
        content.push('\n');
        
        fs::write(config_path, content).await?;
        
        Ok(())
    }

    // API key management removed in simplified version

    fn get_config_path() -> Result<PathBuf> {
        // Check for environment variable override (used in testing)
        if let Ok(config_dir) = std::env::var("MEDIA_MANAGER_CONFIG_DIR") {
            return Ok(PathBuf::from(config_dir).join("config.json"));
        }

        // Default to system config directory
        let proj_dirs = ProjectDirs::from("com", "media-manager", "config")
            .ok_or_else(|| std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "Could not determine project directories"
            ))?;

        Ok(proj_dirs.config_dir().join("config.json"))
    }

    #[cfg(test)]
    pub fn with_config_dir(config_dir: PathBuf) -> Self {
        std::env::set_var("MEDIA_MANAGER_CONFIG_DIR", config_dir);
        Self::default()
    }
}
