use std::path::Path;
use tokio::process::Command;
use serde::{Deserialize, Serialize};
use crate::error::{MediaManagerError, Result};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubtitleStream {
    pub index: u32,
    pub language: Option<String>,
    pub title: Option<String>,
    pub codec: String,  // "srt", "ass", "pgs", etc.
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaMetadata {
    pub duration_seconds: Option<f64>,
    pub width: Option<u32>,
    pub height: Option<u32>,
    pub codec_name: Option<String>,
    pub subtitle_streams: Vec<SubtitleStream>,
    // Add more fields as needed from ffprobe output
}

impl MediaMetadata {
    /// Checks if ffprobe is available on the system.
    pub async fn check_ffprobe() -> Result<()> {
        let output = Command::new("ffprobe")
            .arg("-version")
            .output()
            .await
            .map_err(|e| {
                if e.kind() == std::io::ErrorKind::NotFound {
                    MediaManagerError::FfprobeNotFound
                } else {
                    MediaManagerError::Io(e)
                }
            })?;

        if output.status.success() {
            Ok(())
        } else {
            Err(MediaManagerError::FfprobeError(
                String::from_utf8_lossy(&output.stderr).into_owned(),
            ))
        }
    }

    /// Invokes ffprobe as a subprocess to extract metadata.
    pub async fn from_file(file_path: &Path) -> Result<Self> {
        let output = Command::new("ffprobe")
            .arg("-v")
            .arg("quiet")
            .arg("-print_format")
            .arg("json")
            .arg("-show_format")
            .arg("-show_streams")
            .arg(file_path)
            .output()
            .await
            .map_err(|e| {
                if e.kind() == std::io::ErrorKind::NotFound {
                    MediaManagerError::FfprobeNotFound
                } else {
                    MediaManagerError::Io(e)
                }
            })?;

        if !output.status.success() {
            return Err(MediaManagerError::FfprobeError(
                String::from_utf8_lossy(&output.stderr).into_owned(),
            ));
        }

        let ffprobe_json: serde_json::Value = serde_json::from_slice(&output.stdout)?;

        let format = ffprobe_json.get("format");
        let streams = ffprobe_json.get("streams").and_then(|s| s.as_array());

        let duration_seconds = format
            .and_then(|f| f.get("duration"))
            .and_then(|d| d.as_str())
            .and_then(|s| s.parse::<f64>().ok());

        let mut width = None;
        let mut height = None;
        let mut codec_name = None;
        let mut subtitle_streams = Vec::new();

        if let Some(streams_array) = streams {
            // Find the first video stream for resolution and codec
            for stream in streams_array {
                if let Some(codec_type) = stream.get("codec_type").and_then(|t| t.as_str()) {
                    if codec_type == "video" {
                        width = stream.get("width").and_then(|w| w.as_u64()).map(|w| w as u32);
                        height = stream.get("height").and_then(|h| h.as_u64()).map(|h| h as u32);
                        codec_name = stream.get("codec_name").and_then(|c| c.as_str()).map(|s| s.to_string());
                    } else if codec_type == "subtitle" {
                        let index = stream.get("index").and_then(|i| i.as_u64()).map(|i| i as u32).unwrap_or(0);
                        let language = stream.get("tags")
                            .and_then(|t| t.get("language"))
                            .and_then(|l| l.as_str())
                            .map(|s| s.to_string());
                        let title = stream.get("tags")
                            .and_then(|t| t.get("title"))
                            .and_then(|t| t.as_str())
                            .map(|s| s.to_string());
                        let codec = stream.get("codec_name")
                            .and_then(|c| c.as_str())
                            .unwrap_or("unknown")
                            .to_string();
                            
                        subtitle_streams.push(SubtitleStream {
                            index,
                            language,
                            title,
                            codec,
                        });
                    }
                }
            }
        }

        Ok(MediaMetadata {
            duration_seconds,
            width,
            height,
            codec_name,
            subtitle_streams,
        })
    }
}
