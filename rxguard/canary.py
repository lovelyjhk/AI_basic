from __future__ import annotations

import json
import os
import random
import string
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

import xxhash

from .config import AppConfig


CANARY_META = "canaries.json"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def random_bytes(n: int) -> bytes:
    return os.urandom(n)


def random_name(prefix: str, ext: str) -> str:
    letters = string.ascii_lowercase
    return f"{prefix}-" + "".join(random.choice(letters) for _ in range(8)) + ext


@dataclass
class Canary:
    path: str
    hash: str


class CanaryManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.repo_canary_dir = Path(config.canary_dir)
        ensure_dir(str(self.repo_canary_dir))
        self.meta_path = self.repo_canary_dir / CANARY_META

    def _load_meta(self) -> List[Canary]:
        if not self.meta_path.exists():
            return []
        with open(self.meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Canary(**c) for c in data]

    def _save_meta(self, canaries: List[Canary]) -> None:
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in canaries], f, ensure_ascii=False, indent=2)

    def deploy(self, per_dir: int = 3) -> List[Canary]:
        canaries: List[Canary] = []
        for d in self.config.data_dirs:
            ensure_dir(d)
            for i in range(per_dir):
                ext = random.choice([".xlsx", ".pdf", ".dcm", ".docx", ".txt"])  # medical-relevant decoys
                name = random_name("canary", ext)
                path = os.path.join(d, name)
                content = random_bytes(2048)
                with open(path, "wb") as f:
                    f.write(content)
                canaries.append(Canary(path=path, hash=xxhash.xxh64_hexdigest(content)))
        self._save_meta(canaries)
        return canaries

    def check(self) -> int:
        """Return the number of tampered canaries."""
        canaries = self._load_meta()
        tampered = 0
        for c in canaries:
            if not os.path.exists(c.path):
                tampered += 1
                continue
            try:
                with open(c.path, "rb") as f:
                    data = f.read()
                h = xxhash.xxh64_hexdigest(data)
                if h != c.hash:
                    tampered += 1
            except Exception:
                tampered += 1
        return tampered

