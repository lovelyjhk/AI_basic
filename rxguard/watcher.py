from __future__ import annotations

import math
import os
import queue
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from .config import AppConfig
from .logging_utils import get_logger
from .canary import CanaryManager
from .repo import Repo


logger = get_logger(__name__)


def shannon_entropy(sample: bytes) -> float:
    if not sample:
        return 0.0
    counts = Counter(sample)
    total = len(sample)
    entropy = 0.0
    for _, c in counts.items():
        p = c / total
        entropy -= p * math.log2(p)
    return entropy


class EventBuffer(FileSystemEventHandler):
    def __init__(self, q: "queue.Queue[FileSystemEvent]"):
        super().__init__()
        self.q = q

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self.q.put(event)

    def on_moved(self, event: FileSystemEvent):
        if not event.is_directory:
            self.q.put(event)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self.q.put(event)


@dataclass
class DetectionResult:
    surge: bool
    high_entropy: bool
    suspicious_ext: bool
    canary_tamper: bool

    def is_alert(self) -> bool:
        return self.surge or self.high_entropy or self.suspicious_ext or self.canary_tamper


class RansomwareWatcher:
    def __init__(self, config: AppConfig, repo: Repo, canary_manager: CanaryManager):
        self.config = config
        self.repo = repo
        self.canary = canary_manager
        self.q: "queue.Queue[FileSystemEvent]" = queue.Queue()
        self.observer = Observer()
        self.modified_window: Deque[float] = deque(maxlen=10000)

    def start(self) -> None:
        handler = EventBuffer(self.q)
        for d in self.config.data_dirs:
            self.observer.schedule(handler, d, recursive=True)
        self.observer.start()
        logger.info("Watcher started for %d directories", len(self.config.data_dirs))

    def stop(self) -> None:
        self.observer.stop()
        self.observer.join(timeout=5)

    def _detect(self, paths: List[str]) -> DetectionResult:
        now = time.time()
        self.modified_window.extend([now] * len(paths))
        # surge detection in last 60s
        cutoff = now - 60
        while self.modified_window and self.modified_window[0] < cutoff:
            self.modified_window.popleft()
        surge = len(self.modified_window) >= self.config.modification_rate_threshold_per_minute

        high_entropy = False
        suspicious_ext = False
        for p in paths[:20]:  # sample up to 20 files
            try:
                _, ext = os.path.splitext(p)
                if ext in (self.config.suspicious_extension_suffixes or []):
                    suspicious_ext = True
                with open(p, "rb") as f:
                    sample = f.read(4096)
                ent = shannon_entropy(sample)
                if ent >= self.config.entropy_threshold_modified_sample:
                    high_entropy = True
            except Exception:
                continue

        canary_tamper = self.canary.check() > 0
        return DetectionResult(surge=surge, high_entropy=high_entropy, suspicious_ext=suspicious_ext, canary_tamper=canary_tamper)

    def run(self) -> None:
        self.start()
        try:
            while True:
                paths: List[str] = []
                try:
                    # batch events to reduce overhead
                    for _ in range(100):
                        ev = self.q.get(timeout=1)
                        if getattr(ev, "src_path", None):
                            paths.append(ev.src_path)
                        if getattr(ev, "dest_path", None):
                            paths.append(ev.dest_path)
                except queue.Empty:
                    pass

                if not paths:
                    continue

                result = self._detect(paths)
                if result.is_alert():
                    logger.warning("Suspicious activity detected: %s", result)
                    # Immediate snapshot for containment
                    try:
                        self.repo.create_snapshot(label="auto-alert")
                    except Exception as e:
                        logger.error("Snapshot on alert failed: %s", e)
                    # short cooldown to avoid storm
                    time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Watcher stopped by user")
        finally:
            self.stop()

