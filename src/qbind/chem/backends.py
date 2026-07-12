"""Single-point energy backends. All expose `.name` and `.energy(Geometry)->Ha`.

* AnalyticBackend  -- pure Python, no deps: lets the whole molecular pipeline
  run and be tested here. DFT vs correlated is modelled by a metal-coordination
  term so the delta analysis has something real to chew on.
* DFTBackend       -- pyscf UKS (the classical majority-of-fragments path).
* CASSCFBackend    -- pyscf AVAS + CASSCF on metal-containing clusters; DFT
  otherwise. The classical correlated solver: answers the research question
  with NO quantum computer. Use this first.
* SQDBackend       -- reuses the qadv SQD kernel; warranted only when the active
  space exceeds classical exact reach.

Correlated backends fall back to DFT on fragments with no metal (a closed-shell
ligand needs no multireference treatment), which keeps them robust and honest.
"""
from __future__ import annotations

import math

from .geometry import Geometry, metal_symbols_from_labels

DEFAULT_METALS = ("Fe", "Mn", "Co", "Ni", "Cu", "Zn", "Mo", "Ru", "V", "Cr")


# --------------------------------------------------------------------------- #
# Analytic (dependency-free) -- for tests and pipeline validation only.
# --------------------------------------------------------------------------- #
class AnalyticBackend:
    """Toy but deterministic energy: pairwise 1/r with pseudo-charges, plus an
    optional metal-coordination stabilisation that models the correlation
    correction DFT misses. NOT physical -- it validates the machinery."""

    _Z = {"H": 1, "C": 4, "N": 5, "O": 6, "S": 6, "F": 7, "P": 5, "Cl": 7}

    def __init__(self, name="analytic", metal_pull: float = 0.0,
                 metals=DEFAULT_METALS, coord_cutoff: float = 2.6,
                 scale: float = 6e-4):
        self.name = name
        self.metal_pull = metal_pull        # extra metal-ligand stabilisation (Ha)
        self.metals = set(metals)
        self.coord_cutoff = coord_cutoff
        self.scale = scale                  # keeps interaction energies ~ kcal/mol scale

    def _z(self, el: str) -> float:
        return float(self._Z.get(el, 8 if el in self.metals else 4))

    def energy(self, geom: Geometry) -> float:
        # Toy attractive pairwise model in pseudo-Hartree. Intra-fragment pairs
        # cancel in E(AB)-E(A)-E(B), so only cross A-B pairs set the interaction.
        atoms = geom.atoms
        e = 0.0
        for i in range(len(atoms)):
            ei, ri = atoms[i]
            for j in range(i + 1, len(atoms)):
                ej, rj = atoms[j]
                d = math.dist(ri, rj)
                if d < 1e-6:
                    continue
                e -= self._z(ei) * self._z(ej) / d * self.scale     # attractive toy term
                if (self.metal_pull and d < self.coord_cutoff
                        and (ei in self.metals) ^ (ej in self.metals)):
                    e -= self.metal_pull
        return e


# --------------------------------------------------------------------------- #
# Real backends (lazy imports; only needed for genuine chemistry).
# --------------------------------------------------------------------------- #
def _build_mol(geom: Geometry, basis: str, max_mem_frac: float = 0.5):
    from pyscf import gto
    return gto.M(atom=geom.to_pyscf_atom(), basis=basis, charge=geom.charge,
                 spin=geom.spin, verbose=0)


class DFTBackend:  # pragma: no cover - needs pyscf
    name = "dft"

    def __init__(self, xc: str = "wb97x-d", basis: str = "def2-SVP"):
        self.xc = xc
        self.basis = basis

    def energy(self, geom: Geometry) -> float:
        from pyscf import dft
        mol = _build_mol(geom, self.basis)
        ks = dft.UKS(mol).density_fit()
        ks.xc = self.xc
        ks.max_cycle = 200
        e = ks.kernel()
        if not ks.converged:
            ks = ks.newton()
            e = ks.kernel()
        return float(e)


class CASSCFBackend:  # pragma: no cover - needs pyscf
    name = "casscf"

    def __init__(self, ao_labels=("Fe 3d", "Fe 4d"), basis: str = "def2-SVP",
                 xc: str = "wb97x-d", avas_threshold: float = 0.2):
        self.ao_labels = list(ao_labels)
        self.basis = basis
        self.avas_threshold = avas_threshold
        self.metals = metal_symbols_from_labels(self.ao_labels)
        self._dft = DFTBackend(xc=xc, basis=basis)

    def energy(self, geom: Geometry) -> float:
        if not geom.has_any(self.metals):
            return self._dft.energy(geom)       # no metal -> DFT suffices
        from pyscf import mcscf, scf
        from pyscf.mcscf import avas
        mol = _build_mol(geom, self.basis)
        mf = scf.ROHF(mol).density_fit()
        mf.max_cycle = 200
        mf.kernel()
        ncas, nelecas, mo = avas.avas(mf, self.ao_labels,
                                      threshold=self.avas_threshold, canonicalize=True)
        mc = mcscf.CASSCF(mf, int(ncas), int(nelecas))
        mc.max_cycle_macro = 100
        e = mc.kernel(mo)[0]
        return float(e)


class SQDBackend:  # pragma: no cover - needs qadv[science]
    name = "sqd"

    def __init__(self, ao_labels=("Fe 3d", "Fe 4d"), basis: str = "def2-SVP",
                 xc: str = "wb97x-d", subspace_dim: int = 20000, shots: int = 100_000):
        self.ao_labels = list(ao_labels)
        self.basis = basis
        self.metals = metal_symbols_from_labels(self.ao_labels)
        self.subspace_dim = subspace_dim
        self.shots = shots
        self._dft = DFTBackend(xc=xc, basis=basis)

    def energy(self, geom: Geometry) -> float:
        if not geom.has_any(self.metals):
            return self._dft.energy(geom)
        import tempfile
        from pyscf import scf
        from qadv.runtime import Context
        from qadv.settings import Settings
        from qadv.chem import active_space
        from qadv.constants import STATEVECTOR_WALL_QUBITS
        from qadv.quantum import ansatz, sampling, sqd

        ctx = Context(Settings.from_env(tempfile.mkdtemp()))
        mol = _build_mol(geom, self.basis)
        mf = scf.ROHF(mol).density_fit()
        mf.max_cycle = 200
        mf.kernel()
        # want_casci=False: we want the SQD energy itself, not the exact anchor.
        a = active_space.build(ctx, mf, self.ao_labels, spin=geom.spin, want_casci=False)
        circ = ansatz.build_lucj(ctx, mf, a)
        if circ is None:
            return self._dft.energy(geom)
        bits = (sampling.statevector(ctx, circ, self.shots)
                if a.n_qubits <= STATEVECTOR_WALL_QUBITS
                else sampling.mps(ctx, circ, self.shots))
        return sqd.diagonalize(ctx, a, bits, self.subspace_dim)


def make_backend(kind: str, **kw):
    kind = kind.lower()
    if kind == "analytic":
        return AnalyticBackend(**kw)
    if kind == "analytic-correlated":
        return AnalyticBackend(name="analytic-correlated",
                               metal_pull=kw.pop("metal_pull", 1.5), **kw)
    if kind == "dft":
        return DFTBackend(**kw)
    if kind == "casscf":
        return CASSCFBackend(**kw)
    if kind == "sqd":
        return SQDBackend(**kw)
    raise ValueError(f"unknown backend '{kind}'")
