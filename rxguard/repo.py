from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from tqdm import tqdm

from .config import AppConfig
from .crypto_utils import load_or_create_master_key, encrypt_chunk, decrypt_chunk
from .logging_utils import get_logger


logger = get_logger(__name__)


SNAPSHOT_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iter_file_chunks(path: str, chunk_size: int) -> Iterable[bytes]:
    with open(path, "rb") as f:
        while True:
            buf = f.read(chunk_size)
            if not buf:
                break
            yield buf


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


@dataclass
class FileEntry:
    path: str
    size: int
    mtime_ns: int
    chunks: List[str]


@dataclass
class Snapshot:
    id: str
    created_at: str
    version: int
    label: Optional[str]
    files: List[FileEntry]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class Repo:
    def __init__(self, config: AppConfig):
        self.config = config
        self.repo_dir = Path(config.repo_dir)
        self.chunks_dir = Path(config.chunks_dir)
        self.manifest_dir = Path(config.manifest_dir)
        self.key_file = Path(config.key_file)
        self.master_key: Optional[bytes] = None

    @staticmethod
    def init_repo(config: AppConfig) -> "Repo":
        ensure_dir(config.repo_dir)
        ensure_dir(config.chunks_dir)
        ensure_dir(config.manifest_dir)
        ensure_dir(os.path.dirname(config.key_file))
        ensure_dir(config.canary_dir)
        ensure_dir(os.path.dirname(config.log_file))
        master_key = load_or_create_master_key(config.key_file)
        logger.info("Initialized repo at %s", config.repo_dir)
        repo = Repo(config)
        repo.master_key = master_key
        return repo

    def load(self) -> None:
        self.master_key = load_or_create_master_key(self.config.key_file)

    def _chunk_path(self, chunk_hash_hex: str) -> Path:
        return self.chunks_dir / chunk_hash_hex[:2] / f"{chunk_hash_hex}.bin"

    def has_chunk(self, chunk_hash_hex: str) -> bool:
        return self._chunk_path(chunk_hash_hex).exists()

    def store_chunk(self, chunk_hash_hex: str, ciphertext: bytes) -> None:
        path = self._chunk_path(chunk_hash_hex)
        ensure_dir(path.parent)
        if not path.exists():
            with open(path, "wb") as f:
                f.write(ciphertext)

    def load_chunk(self, chunk_hash_hex: str) -> bytes:
        path = self._chunk_path(chunk_hash_hex)
        with open(path, "rb") as f:
            return f.read()

    def _scan_files(self) -> List[str]:
        files: List[str] = []
        for d in self.config.data_dirs:
            for root, _, filenames in os.walk(d):
                for name in filenames:
                    full = os.path.join(root, name)
                    try:
                        # skip our own repo directory if nested under data_dirs
                        if os.path.commonpath([full, self.repo_dir]) == str(self.repo_dir):
                            continue
                    except Exception:
                        pass
                    files.append(full)
        return files

    def create_snapshot(self, label: Optional[str] = None) -> Snapshot:
        if self.master_key is None:
            self.load()
        ensure_dir(self.manifest_dir)
        files = self._scan_files()
        file_entries: List[FileEntry] = []

        for path in tqdm(files, desc="Snapshotting", unit="file"):
            try:
                stat = os.stat(path)
                chunks: List[str] = []
                for chunk in iter_file_chunks(path, self.config.chunk_size_bytes):
                    chunk_hash_hex, ciphertext = encrypt_chunk(chunk, self.master_key)  # type: ignore[arg-type]
                    if not self.has_chunk(chunk_hash_hex):
                        self.store_chunk(chunk_hash_hex, ciphertext)
                    chunks.append(chunk_hash_hex)
                file_entries.append(
                    FileEntry(path=path, size=stat.st_size, mtime_ns=stat.st_mtime_ns, chunks=chunks)
                )
            except (PermissionError, FileNotFoundError):
                continue

        snap_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snapshot = Snapshot(
            id=snap_id,
            created_at=utc_now_iso(),
            version=SNAPSHOT_VERSION,
            label=label,
            files=file_entries,
        )
        manifest_path = self.manifest_dir / f"{snap_id}.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(snapshot.to_json())
        logger.info("Created snapshot %s with %d files", snap_id, len(file_entries))
        return snapshot

    def list_snapshots(self) -> List[str]:
        if not self.manifest_dir.exists():
            return []
        snaps = sorted([p.stem for p in self.manifest_dir.glob("*.json")])
        return snaps

    def load_snapshot(self, snapshot_id: str) -> Snapshot:
        path = self.manifest_dir / f"{snapshot_id}.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        files = [FileEntry(**fe) for fe in data["files"]]
        return Snapshot(
            id=data["id"],
            created_at=data["created_at"],
            version=data["version"],
            label=data.get("label"),
            files=files,
        )

    def restore(self, snapshot_id: str, dest_dir: str, include_prefixes: Optional[List[str]] = None) -> None:
        if self.master_key is None:
            self.load()
        snapshot = self.load_snapshot(snapshot_id)
        ensure_dir(dest_dir)
        for fe in tqdm(snapshot.files, desc="Restoring", unit="file"):
            if include_prefixes and not any(fe.path.startswith(p) for p in include_prefixes):
                continue
            rel = os.path.relpath(fe.path, start=os.path.commonpath(self.config.data_dirs))
            out_path = Path(dest_dir) / rel
            ensure_dir(out_path.parent)
            with open(out_path, "wb") as out:
                for ch in fe.chunks:
                    ciphertext = self.load_chunk(ch)
                    plaintext = decrypt_chunk(ch, ciphertext, self.master_key)  # type: ignore[arg-type]
                    out.write(plaintext)

    def verify(self, snapshot_id: Optional[str] = None) -> Tuple[int, int]:
        """Verify manifests and chunk presence.

        Returns (num_files, missing_chunks)
        """
        snap_ids = [snapshot_id] if snapshot_id else self.list_snapshots()
        missing = 0
        files = 0
        for sid in snap_ids:
            snap = self.load_snapshot(sid)
            files += len(snap.files)
            for fe in snap.files:
                for ch in fe.chunks:
                    if not self.has_chunk(ch):
                        missing += 1
        return files, missing

