"""Runtime side effects: output dir, logging, decision journal, checkpoints.

Injected into the orchestrator so the scientific code stays free of I/O and the
pipeline is testable against a tmp directory.
"""
from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any


class Run:
    def __init__(self, outdir: str | Path):
        self.outdir = Path(outdir)
        self.figures = self.outdir / "figures"
        self.checkpoints = self.outdir / "checkpoints"
        self.results = self.outdir / "results"
        for d in (self.figures, self.checkpoints, self.results):
            d.mkdir(parents=True, exist_ok=True)
        self.decisions_file = self.outdir / "DECISIONS.md"
        self._logger = self._make_logger(self.outdir / "run.log")
        self.log(f"run initialised at {self.outdir}")

    @staticmethod
    def _make_logger(logfile: Path) -> logging.Logger:
        logger = logging.getLogger(f"qbind[{logfile.parent.name}]")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s",
                                datefmt="%H:%M:%S")
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)
        try:
            fh = logging.FileHandler(logfile, encoding="utf-8")
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        except Exception:
            pass
        logger.propagate = False
        return logger

    def log(self, msg: str, level: str = "INFO") -> None:
        self._logger.log(getattr(logging, level, logging.INFO), msg)

    def decide(self, what: str, choice: str, why: str) -> None:
        self.log(f"DECISION: {what} -> {choice} ({why})")
        try:
            with open(self.decisions_file, "a", encoding="utf-8") as f:
                f.write(f"- **{what}** -> `{choice}`  \n  _{why}_\n")
        except Exception:
            pass

    def save(self, name: str, obj: Any) -> None:
        with open(self.checkpoints / f"{name}.pkl", "wb") as f:
            pickle.dump(obj, f)
        self.log(f"checkpoint saved: {name}")

    def load(self, name: str) -> Any | None:
        p = self.checkpoints / f"{name}.pkl"
        if p.exists():
            self.log(f"resuming from checkpoint: {name}")
            with open(p, "rb") as f:
                return pickle.load(f)
        return None

    def write_json(self, name: str, obj: Any) -> Path:
        p = self.results / name
        p.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
        return p
