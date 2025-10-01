use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::path::PathBuf;

mod config;
mod crypto;
mod backup;
mod restore;
mod monitor;
mod ai;

use crate::config::AppConfig;

#[derive(Parser, Debug)]
#[command(name = "sentinel", version, about = "AI-assisted ransomware defense CLI", long_about = None)]
struct Cli {
    /// Path to configuration file (TOML)
    #[arg(short, long, global = true)]
    config: Option<PathBuf>,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Generate a new AES-256 key file
    Keygen {
        /// Output key path (overrides config)
        #[arg(short, long)]
        out: Option<PathBuf>,
        /// Overwrite if exists
        #[arg(long)]
        force: bool,
    },
    /// Encrypt a file (writes .enc by default)
    Encrypt {
        /// Source file to encrypt
        input: PathBuf,
        /// Output file (defaults to input + .enc)
        #[arg(short, long)]
        out: Option<PathBuf>,
        /// Key file (overrides config)
        #[arg(short = 'k', long = "key")] 
        key_path: Option<PathBuf>,
    },
    /// Decrypt a file (removes .enc by default)
    Decrypt {
        /// Encrypted input file
        input: PathBuf,
        /// Output file (defaults to strip .enc)
        #[arg(short, long)]
        out: Option<PathBuf>,
        /// Key file (overrides config)
        #[arg(short = 'k', long = "key")] 
        key_path: Option<PathBuf>,
    },
    /// Run incremental backup snapshot
    Backup {
        /// Source directory (overrides config)
        #[arg(short, long)]
        source: Option<PathBuf>,
        /// Store directory (overrides config)
        #[arg(short, long)]
        store: Option<PathBuf>,
    },
    /// Restore latest snapshot
    Restore {
        /// Target restore directory (overrides config)
        #[arg(short, long)]
        target: Option<PathBuf>,
        /// Store directory (overrides config)
        #[arg(short, long)]
        store: Option<PathBuf>,
    },
    /// Monitor filesystem and consult AI heuristics
    Monitor {
        /// Directory to watch (overrides config)
        #[arg(short, long)]
        watch: Option<PathBuf>,
    },
    /// Print resolved configuration
    Config,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    let cfg_path = cli.config.unwrap_or_else(|| PathBuf::from("/workspace/configs/sentinel.toml"));
    let cfg = AppConfig::load(&cfg_path).with_context(|| format!("Failed to load config at {}", cfg_path.display()))?;

    match cli.command {
        Commands::Keygen { out, force } => {
            let out_path = out.unwrap_or_else(|| cfg.key_path.clone());
            crypto::generate_key_file(&out_path, force)?;
            println!("Key generated: {}", out_path.display());
        }
        Commands::Encrypt { input, out, key_path } => {
            let key_path = key_path.unwrap_or_else(|| cfg.key_path.clone());
            let out_path = out.unwrap_or_else(|| input.with_extension(format!("{}", input.extension().and_then(|e| e.to_str()).map(|s| format!("{}.", s)).unwrap_or_default() + "enc")));
            crypto::encrypt_file(&key_path, &input, &out_path)?;
            println!("Encrypted: {} -> {}", input.display(), out_path.display());
        }
        Commands::Decrypt { input, out, key_path } => {
            let key_path = key_path.unwrap_or_else(|| cfg.key_path.clone());
            let out_path = out.unwrap_or_else(|| {
                if let Some(name) = input.file_name().and_then(|n| n.to_str()) {
                    if let Some(stripped) = name.strip_suffix(".enc") {
                        let mut p = input.clone();
                        p.set_file_name(stripped);
                        return p;
                    }
                }
                input.with_extension("dec")
            });
            crypto::decrypt_file(&key_path, &input, &out_path)?;
            println!("Decrypted: {} -> {}", input.display(), out_path.display());
        }
        Commands::Backup { source, store } => {
            let src = source.unwrap_or_else(|| cfg.source_dir.clone());
            let sto = store.unwrap_or_else(|| cfg.store_dir.clone());
            backup::run_backup(&cfg, &src, &sto).await?;
        }
        Commands::Restore { target, store } => {
            let tgt = target.unwrap_or_else(|| cfg.restore_dir.clone());
            let sto = store.unwrap_or_else(|| cfg.store_dir.clone());
            restore::run_restore(&cfg, &sto, &tgt).await?;
        }
        Commands::Monitor { watch } => {
            let dir = watch.unwrap_or_else(|| cfg.source_dir.clone());
            monitor::run_monitor(&cfg, &dir).await?;
        }
        Commands::Config => {
            println!("{}", serde_json::to_string_pretty(&cfg)?);
        }
    }

    Ok(())
}

