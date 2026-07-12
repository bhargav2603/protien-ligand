"""Geometry sanity: atom counts and bond lengths (no heavy deps needed)."""
import numpy as np
import pytest

from qadv.chem import geometry as G


def _dist(a, b):
    return float(np.linalg.norm(np.array(a[1]) - np.array(b[1])))


def _nearest(atoms, atom):
    return min(_dist(atom, b) for b in atoms if b is not atom)


def test_iron_porphine_composition():
    atoms = G.iron_porphine()
    counts = {}
    for el, _ in atoms:
        counts[el] = counts.get(el, 0) + 1
    assert counts == {"Fe": 1, "C": 20, "N": 4, "H": 12}
    assert len(atoms) == 37


def test_fe_n_bond_length():
    atoms = G.iron_porphine()
    fe = next(a for a in atoms if a[0] == "Fe")
    n = next(a for a in atoms if a[0] == "N")
    assert _dist(fe, n) == pytest.approx(2.00, abs=0.02)


def test_compound_i_composition_and_axials():
    atoms = G.compound_i()
    counts = {}
    for el, _ in atoms:
        counts[el] = counts.get(el, 0) + 1
    assert counts == {"Fe": 1, "C": 20, "N": 4, "H": 13, "O": 1, "S": 1}
    fe = next(a for a in atoms if a[0] == "Fe")
    o = next(a for a in atoms if a[0] == "O")
    s = next(a for a in atoms if a[0] == "S")
    assert _dist(fe, o) == pytest.approx(1.63, abs=0.02)   # Fe=O
    assert _dist(fe, s) == pytest.approx(2.50, abs=0.02)   # Fe-S


def test_no_atomic_clashes():
    for builder in (G.iron_porphine, G.compound_i):
        atoms = builder()
        for a in atoms:
            assert _nearest(atoms, a) > 0.8, f"atoms too close in {builder.__name__}"
