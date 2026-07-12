"""The single user-facing input file.

`input.json` at the repo root is the ONE file a user edits. It is loaded once
into a typed, validated `RunInput` and dispatched into the existing injected
objects (`Config`, `StudySpec` via `run_molecular`) -- no globals, no code edits.

Keep RUN PARAMETERS here (mode, backend, geometries, affinities, seeds). Do NOT
put physics constants or code invariants here (those live in constants.py); they
are not "inputs" and must not be user-tunable.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

_VALID_MODES = ("reference", "molecular")
_VALID_BACKENDS = ("analytic", "dft", "casscf", "sqd")


@dataclass
class RunInput:
    mode: str = "molecular"                 # "reference" | "molecular"
    output_dir: str = "./out"
    backend: str = "analytic"               # molecular backend
    study_file: str | None = None           # molecular: path to a study.json
    reference: dict = field(default_factory=dict)  # reference-mode knobs
    _base: Path = field(default=Path("."), repr=False)

    # -- load / validate --------------------------------------------------- #
    @classmethod
    def load(cls, path: str | Path) -> "RunInput":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"input file not found: {path} (create one, e.g. copy input.json)")
        data = json.loads(path.read_text(encoding="utf-8"))
        obj = cls(
            mode=str(data.get("mode", "molecular")).lower(),
            output_dir=str(data.get("output_dir", "./out")),
            backend=str(data.get("backend", "analytic")).lower(),
            study_file=data.get("study_file"),
            reference=dict(data.get("reference", {})),
            _base=path.parent,
        )
        obj._validate()
        return obj

    def _validate(self) -> None:
        if self.mode not in _VALID_MODES:
            raise ValueError(f"mode must be one of {_VALID_MODES}, got '{self.mode}'")
        if self.mode == "molecular" and self.backend not in _VALID_BACKENDS:
            raise ValueError(
                f"backend must be one of {_VALID_BACKENDS}, got '{self.backend}'")

    def _resolved_study(self) -> str | None:
        """study_file is relative to the input.json location, so paths stay portable."""
        if not self.study_file:
            return None
        p = Path(self.study_file)
        return str(p if p.is_absolute() else (self._base / p))

    # -- dispatch ---------------------------------------------------------- #
    def execute(self):
        """Run the study described by this input. Returns (result, report, figs)."""
        if self.mode == "reference":
            from . import run
            from .config import Config, ReferenceModel
            cfg = Config(reference=ReferenceModel(**self.reference))
            return run(self.output_dir, cfg)

        from . import run_molecular
        return run_molecular(self.output_dir, backend=self.backend,
                             study_file=self._resolved_study())


def run_from_input(path: str | Path = "input.json"):
    return RunInput.load(path).execute()
