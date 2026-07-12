"""Domain model. Immutable-ish typed records that flow through the pipeline.

Energies are binding free energies (dG) in kcal/mol; more negative = tighter.
The pipeline's job is to produce, per ligand, a `baseline_score` (classical
only) and a `corrected_score` (with the strongly-correlated fragment treated by
the quantum/correlated solver), then quantify how the ranking changed.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FragmentSpec:
    """A fragment of the QM region. `is_strongly_correlated` picks the one (few)
    fragment(s) routed to the quantum/correlated solver instead of DFT/MP2."""
    name: str
    atom_indices: tuple[int, ...]
    is_strongly_correlated: bool = False
    # Natural-orbital-occupation-based multireference diagnostic, if computed.
    no_occupations: tuple[float, ...] = ()

    @property
    def multireference_score(self) -> float:
        """Fraction of active NOs with occupation in the strongly-correlated
        window (0.02, 1.98). ~0 => single-reference; larger => needs correlation."""
        if not self.no_occupations:
            return 0.0
        n = sum(1 for o in self.no_occupations if 0.02 < o < 1.98)
        return n / len(self.no_occupations)


@dataclass(frozen=True)
class Ligand:
    ligand_id: str
    name: str
    smiles: str = ""
    experimental_dg: float | None = None      # measured dG (kcal/mol), if known
    coordinates_fragment: bool = False        # does it contact the correlated center?


@dataclass(frozen=True)
class FragmentInteraction:
    """Per-ligand interaction energy of ONE fragment, both ways of computing it."""
    ligand_id: str
    fragment_name: str
    classical_term: float                     # HF/DFT/MP2 value (kcal/mol)
    correlated_term: float | None = None      # SQD/CASSCF value (kcal/mol)


@dataclass(frozen=True)
class LigandScore:
    ligand_id: str
    baseline_score: float                     # classical-only dG estimate
    corrected_score: float                    # quantum-corrected dG estimate
    experimental_dg: float | None = None

    @property
    def delta(self) -> float:
        """Correction applied by the correlated solver (corrected - baseline)."""
        return self.corrected_score - self.baseline_score


@dataclass
class StudyResult:
    target_name: str
    pocket: str
    scores: list[LigandScore] = field(default_factory=list)
    fragments: list[FragmentSpec] = field(default_factory=list)
    solver: str = "reference"                 # which correlated solver was used
    coordinating_ids: list[str] = field(default_factory=list)  # contact the strong fragment
    notes: list[str] = field(default_factory=list)
