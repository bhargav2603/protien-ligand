"""Geometry parsing, cluster carving, and analytic energy (no heavy deps)."""
import pytest

from qbind.chem import cluster
from qbind.chem.backends import AnalyticBackend, make_backend
from qbind.chem.geometry import Geometry, metal_symbols_from_labels, parse_xyz


def test_parse_xyz_with_header():
    g = parse_xyz("2\nwater-ish\nO 0 0 0\nH 0 0 1\n", spin=0)
    assert g.elements == ("O", "H")
    assert g.atoms[1][1] == (0.0, 0.0, 1.0)


def test_parse_xyz_headerless():
    g = parse_xyz("Fe 0 0 0\nC 0 0 2\n")
    assert g.elements == ("Fe", "C")


def test_metal_symbols_from_labels():
    assert metal_symbols_from_labels(["Fe 3d", "Fe 4d", "O 2p"]) == {"Fe", "O"}


def test_has_any_and_subset():
    g = Geometry(atoms=(("Fe", (0, 0, 0)), ("C", (0, 0, 2)), ("O", (0, 0, 3))), spin=4)
    assert g.has_any({"Fe"})
    sub = g.subset([1, 2], charge=0, spin=0)
    assert sub.elements == ("C", "O")


def test_cluster_carve_splits_atoms():
    combined = Geometry(atoms=(("Fe", (0, 0, 0)), ("C", (0, 0, 2)), ("O", (0, 0, 3))), spin=4)
    job = cluster.carve(combined, fragment_indices=[0], ligand_indices=[1, 2],
                        fragment_charge=0, fragment_spin=4,
                        ligand_charge=0, ligand_spin=0, ligand_id="CO")
    assert job.fragment_a.elements == ("Fe",)
    assert job.ligand_b.elements == ("C", "O")
    assert job.complex_ab.elements == ("Fe", "C", "O")


def test_cluster_carve_rejects_overlap():
    combined = Geometry(atoms=(("Fe", (0, 0, 0)), ("C", (0, 0, 2))), spin=4)
    with pytest.raises(ValueError):
        cluster.carve(combined, [0], [0, 1], 0, 4, 0, 0, "x")


def test_analytic_energy_is_deterministic_and_nonadditive():
    b = AnalyticBackend()
    fe = Geometry(atoms=(("Fe", (0, 0, 0)),), spin=4)
    co = Geometry(atoms=(("C", (0, 0, 2)), ("O", (0, 0, 3.13))))
    ab = Geometry(atoms=fe.atoms + co.atoms, spin=4)
    e_int = b.energy(ab) - b.energy(fe) - b.energy(co)
    assert e_int != 0.0                       # interaction is non-trivial
    assert b.energy(ab) == b.energy(ab)       # deterministic


def test_make_backend_unknown_raises():
    with pytest.raises(ValueError):
        make_backend("nope")
