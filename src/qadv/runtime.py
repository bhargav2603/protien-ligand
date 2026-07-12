"""Runtime context: logging, decision journal, RAM guard, checkpoint store.

`Context` is the single dependency the pipeline needs for side effects. Passing
it explicitly (instead of importing module globals) makes every stage unit-
testable with a tmp directory and keeps I/O out of the scientific code.
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

from .settings import Settings


class Context:
    def __init__(self, settings: Settings):
        self.settings = settings
        for d in (settings.checkpoints, settings.results,
                  settings.figures, settings.logs):
            d.mkdir(parents=True, exist_ok=True)
        self._logger = self._make_logger(settings.logs / "run.log")
        self.log(f"project initialised at {settings.proj}")

    # -- logging ----------------------------------------------------------- #
    @staticmethod
    def _make_logger(logfile: Path) -> logging.Logger:
        logger = logging.getLogger(f"qadv[{logfile.parent.parent.name}]")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s",
                                datefmt="%Y-%m-%dT%H:%M:%S")
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)
        try:
            fh = logging.FileHandler(logfile, encoding="utf-8")
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        except Exception:
            pass  # logging must never crash the run
        logger.propagate = False
        return logger

    def log(self, msg: str, level: str = "INFO") -> None:
        self._logger.log(getattr(logging, level, logging.INFO), msg)

    # -- decision journal -------------------------------------------------- #
    def decide(self, what: str, choice: str, why: str) -> None:
        self.log(f"DECISION: {what} -> {choice} ({why})")
        try:
            with open(self.settings.decisions_file, "a", encoding="utf-8") as f:
                f.write(f"- **{what}** -> `{choice}`  \n  _{why}_\n")
        except Exception:
            pass

    # -- resource guard ---------------------------------------------------- #
    def ram_ok(self, on_ceiling=None) -> bool:
        try:
            import psutil
        except Exception:
            return True
        m = psutil.virtual_memory()
        self.log(f"RAM {m.used / 1e9:.1f}/{m.total / 1e9:.1f} GB ({m.percent:.0f}%)")
        if m.percent > self.settings.ram_threshold_pct:
            self.log(f"RAM > {self.settings.ram_threshold_pct:.0f}% -> stop growing "
                     "workload", "WARNING")
            if on_ceiling:
                try:
                    on_ceiling()
                except Exception as e:
                    self.log(f"on_ceiling failed: {e}", "WARNING")
            return False
        return True

    # -- checkpoint store -------------------------------------------------- #
    def save(self, name: str, obj: Any) -> None:
        with open(self.settings.checkpoints / f"{name}.pkl", "wb") as f:
            pickle.dump(obj, f)
        self.log(f"checkpoint saved: {name}")

    def load(self, name: str) -> Any | None:
        p = self.settings.checkpoints / f"{name}.pkl"
        if p.exists():
            self.log(f"resuming from checkpoint: {name}")
            with open(p, "rb") as f:
                return pickle.load(f)
        return None

    # -- misc -------------------------------------------------------------- #
    def gpu_available(self) -> bool:
        try:
            import torch
            return bool(torch.cuda.is_available())
        except Exception:
            return False
