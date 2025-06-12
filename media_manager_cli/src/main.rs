use clap::{Parser, Subcommand};
use std::path::PathBuf;
use media_manager_core::{
    MediaScanner, MediaRenamer, UndoManager,
    MediaFile, UndoData,
    MediaManagerError, Result,
};
use tokio::sync::Mutex;
use std::sync::Arc;
use serde_json::{self, json};

#[derive(Parser, Debug)]
#[command(author, version, about = "Media Manager CLI - Phase 1 Prototype", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Shows CLI version and environment status
    Status,
    /// Scans a directory for media files
    Scan {
        /// Directory to scan (defaults to current directory)
        #[arg(default_value = ".")]
        directory: PathBuf,
    },
    /// Stages a rename operation for a file or pattern
    Rename {
        /// Path to the file or a pattern to match files
        file_or_pattern: String,
        /// Template for the new filename (e.g., "{filename} [{resolution}]")
        template: String,
        /// Preview rename without staging
        #[arg(long)]
        dry_run: bool,
    },
    /// Shows currently staged rename operations
    Preview,
    /// Applies all staged rename operations
    Commit,
    /// Reverts the last committed rename batch
    Undo,
}

// Global state for undo data
type LastUndoData = Arc<Mutex<Option<UndoData>>>;

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init(); // Initialize logging

    let cli = Cli::parse();

    let scanner = MediaScanner::new();
    let renamer = MediaRenamer::new().expect("Failed to initialize MediaRenamer");
    let undo_manager = UndoManager::new()?;

    // Shared state for last undo data
    let last_undo_data: LastUndoData = Arc::new(Mutex::new(undo_manager.load_undo_data().await?));

    match &cli.command {
        Commands::Status => {
            handle_status_command().await?;
        }
        Commands::Scan { directory } => {
            handle_scan_command(&scanner, directory).await?;
        }
        Commands::Rename { file_or_pattern, template, dry_run } => {
            handle_rename_command(
                &scanner,
                &renamer,
                file_or_pattern,
                template,
                *dry_run,
            ).await?;
        }
        Commands::Preview => {
            handle_preview_command(&renamer).await?;
        }
        Commands::Commit => {
            handle_commit_command(
                &renamer,
                &undo_manager,
                last_undo_data.clone(),
            ).await?;
        }
        Commands::Undo => {
            handle_undo_command(&renamer, &undo_manager, last_undo_data.clone()).await?;
        }
    }

    Ok(())
}

// --- CLI Command Handlers (could be moved to cli_commands.rs for larger projects) ---

async fn handle_scan_command(scanner: &MediaScanner, directory: &PathBuf) -> Result<()> {
    let media_files = scanner.scan_directory(directory).await?;

    // Convert MediaFile objects to JSON-serializable format
    let files_json: Vec<serde_json::Value> = media_files.iter().map(|file| {
        let metadata_json = if let Some(meta) = &file.metadata {
            let subtitle_streams: Vec<serde_json::Value> = meta.subtitle_streams.iter().map(|stream| {
                json!({
                    "index": stream.index,
                    "language": stream.language,
                    "title": stream.title,
                    "codec": stream.codec
                })
            }).collect();

            json!({
                "resolution": format!("{}x{}", 
                    meta.width.map_or("N/A".to_string(), |w| w.to_string()),
                    meta.height.map_or("N/A".to_string(), |h| h.to_string())
                ),
                "duration": format!("{:.0}s", meta.duration_seconds.unwrap_or(0.0)),
                "codec": meta.codec_name.as_ref().unwrap_or(&"N/A".to_string()),
                "subtitle_streams": subtitle_streams
            })
        } else {
            json!({
                "resolution": "N/A",
                "duration": "N/A", 
                "codec": "N/A",
                "subtitle_streams": []
            })
        };

        json!({
            "path": file.path.to_string_lossy(),
            "metadata": metadata_json
        })
    }).collect();

    let result = json!({
        "files": files_json,
        "count": media_files.len(),
        "directory": directory.to_string_lossy()
    });

    // Output as JSON
    let mut output = serde_json::to_string_pretty(&result)?;
    output = output.replace("\r\n", "\n");
    output = output.trim().to_string();
    output.push('\n');
    
    print!("{}", output);
    Ok(())
}

async fn handle_rename_command(
    _scanner: &MediaScanner,  // Will be used for pattern matching in future
    renamer: &MediaRenamer,
    file_or_pattern: &str,
    template: &str,
    dry_run: bool,
) -> Result<()> {
    // For prototype, assume file_or_pattern is a single file path for now
    // Future: implement pattern matching for batch rename
    let file_path = PathBuf::from(file_or_pattern);

    if !file_path.exists() {
        return Err(MediaManagerError::FileNotFound(file_path));
    }

    let mut media_file = MediaFile::new(file_path.clone());
    // Get metadata for the single file
    match media_manager_core::metadata::MediaMetadata::from_file(&media_file.path).await {
        Ok(metadata) => media_file.metadata = Some(metadata),
        Err(e) => log::warn!("Could not get metadata for {}: {}", media_file.path.display(), e),
    }

    if dry_run {
        let preview = renamer.preview_rename(&media_file, template)?;
        println!("Rename preview (dry run):");
        println!("From: '{}'", preview.original_path.display());
        println!("To:   '{}'", preview.new_path.display());
        if !preview.is_valid {
            println!("Warning: {}", preview.validation_message.unwrap_or_else(|| "Invalid rename operation".to_string()));
        }
    } else {
        renamer.stage_single_rename(&media_file, template).await?;
        println!("Staged rename operation:");
        handle_preview_command(renamer).await?; // Show preview immediately
        println!("Run 'commit' to apply, or 'rename' again to change.");
    }

    Ok(())
}

async fn handle_preview_command(renamer: &MediaRenamer) -> Result<()> {
    let staged_renames = renamer.load_staged_renames().await?;
    if staged_renames.is_empty() {
        println!("No rename operations currently staged.");
    } else {
        println!("Staged rename operations ({}):", staged_renames.len());
        for (i, staged) in staged_renames.iter().enumerate() {
            println!(
                "{}. '{}' -> '{}'",
                i + 1,
                staged.original_path.display(),
                staged.new_path.display()
            );
        }
    }
    Ok(())
}

async fn handle_commit_command(
    renamer: &MediaRenamer,
    undo_manager: &UndoManager,
    last_undo_data: LastUndoData,
) -> Result<()> {
    let committed_ops = renamer.commit_renames().await?;
    println!("Committing {} staged renames...", committed_ops.len());

    // Save undo data
    let new_undo_data = UndoData { operations: committed_ops };
    undo_manager.save_undo_data(&new_undo_data).await?;
    *last_undo_data.lock().await = Some(new_undo_data);

    println!("Rename operations committed successfully!");
    Ok(())
}

async fn handle_status_command() -> Result<()> {
    use serde_json::json;
    
    // Check if ffprobe is available
    let ffprobe_status = if media_manager_core::metadata::MediaMetadata::check_ffprobe().await.is_ok() {
        "ok"
    } else {
        "not_found"
    };
    
    // Build status
    let status = json!({
        "version": env!("CARGO_PKG_VERSION"),
        "platform": std::env::consts::OS,
        "ffprobe": ffprobe_status,
        "lastOperation": {
            "type": "none",
            "timestamp": chrono::Utc::now().to_rfc3339(),
            "success": true
        }
    });

    // Format JSON with consistent indentation and line endings
    let mut output = serde_json::to_string_pretty(&status)?;
    output = output.replace("\r\n", "\n");
    output = output.trim().to_string();
    output.push('\n');
    
    // Print without any extra formatting
    print!("{}", output);
    Ok(())
}

async fn handle_undo_command(
    renamer: &MediaRenamer,
    undo_manager: &UndoManager,
    last_undo_data: LastUndoData,
) -> Result<()> {
    let mut last_undo_data_lock = last_undo_data.lock().await;
    if let Some(undo_data) = last_undo_data_lock.take() { // Take the data to prevent double undo
        println!("Attempting to undo last batch of {} renames...", undo_data.operations.len());
        renamer.undo_renames(undo_data.operations).await?;
        undo_manager.clear_undo_data().await?; // Clear the undo file after successful undo
        println!("Last rename batch undone successfully!");
    } else {
        println!("No previous rename batch to undo.");
    }
    Ok(())
}

// Subtitle command handlers removed in simplified version
