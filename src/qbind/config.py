"""Pipeline configuration (JSON-backed; no third-party YAML dependency).

One config selects the target, the benchmark, and which implementation to use
for each swappable stage (docking, embedding, correlated solver). The reference
config wires everything to in-repo reference implementations so `qbind run`
produces graphs with no external tools installed.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ReferenceModel:
    """Knobs for the synthetic reference study (plumbing validation only).

    `systematic_bias` is the mean error DFT makes on fragment-coordinating
    ligands that the correlated solver removes. Set it to 0.0 to reproduce the
    honest null result: quantum changes nothing.
    """
    n_ligands: int = 18
    fraction_coordinating: float = 0.4
    systematic_bias: float = 1.8        # kcal/mol, removed by correlated solver
    classical_noise: float = 0.6        # kcal/mol, irreducible
    correlated_noise: float = 0.3       # kcal/mol
    seed: int = 7


@dataclass
class Config:
    target_name: str = "REFERENCE-metalloenzyme"
    pocket: str = "reference-pocket"
    # Implementation selectors: "reference" | "vina" | "pyscf" | "sqd" | "casscf"
    docking: str = "reference"
    embedding: str = "reference"
    correlated_solver: str = "reference"
    # Data sources (used when not in reference mode).
    benchmark_csv: str | None = None
    structure_pdb: str | None = None
    reference: ReferenceModel = field(default_factory=ReferenceModel)

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        ref = ReferenceModel(**data.pop("reference", {}))
        return cls(reference=ref, **data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @property
    def is_reference(self) -> bool:
        return (self.docking == "reference"
                and self.embedding == "reference"
                and self.correlated_solver == "reference")
