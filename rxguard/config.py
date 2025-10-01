from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

import yaml


@dataclass
class AppConfig:
    """Application configuration.

    Paths are stored as strings in YAML for portability.
    """

    repo_dir: str
    data_dirs: List[str]
    key_file: str
    manifest_dir: str
    chunks_dir: str
    canary_dir: str
    log_file: str

    chunk_size_bytes: int = 4 * 1024 * 1024
    modification_rate_threshold_per_minute: int = 200
    entropy_threshold_modified_sample: float = 6.5
    suspicious_extension_suffixes: List[str] = None

    @staticmethod
    def default(base_repo_dir: str, data_dirs: List[str]) -> "AppConfig":
        base = Path(base_repo_dir)
        return AppConfig(
            repo_dir=str(base),
            data_dirs=[str(Path(d)) for d in data_dirs],
            key_file=str(base / "keys" / "master.key"),
            manifest_dir=str(base / "manifests"),
            chunks_dir=str(base / "chunks"),
            canary_dir=str(base / "canaries"),
            log_file=str(base / "logs" / "rxguard.log"),
            suspicious_extension_suffixes=[
                ".locked",
                ".crypt",
                ".crypto",
                ".encrypted",
                ".enc",
            ],
        )

    @staticmethod
    def load(path: str) -> "AppConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return AppConfig(**data)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(asdict(self), f, sort_keys=False, allow_unicode=True)
