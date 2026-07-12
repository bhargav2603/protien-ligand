"""The consistency invariant: baseline and corrected differ ONLY by the
correlated fragment term. If this breaks, the delta stops being a clean
measurement of the quantum correction."""
from qbind.models import FragmentInteraction, Ligand
from qbind.scoring import rescore


def _lig():
    return Ligand("L0", "L0", experimental_dg=-9.0)


def test_delta_equals_only_strong_fragment_correction():
    lig = _lig()
    interactions = [
        FragmentInteraction("L0", "weak1", classical_term=-1.0, correlated_term=None),
        FragmentInteraction("L0", "weak2", classical_term=-0.5, correlated_term=None),
        FragmentInteraction("L0", "metal", classical_term=2.0, correlated_term=-0.5),
    ]
    s = rescore.build_score(lig, docking_score=-7.0, complementarity=-0.3,
                            fragment_interactions=interactions)
    # delta must be exactly (correlated - classical) of the strong fragment.
    assert abs(s.delta - (-0.5 - 2.0)) < 1e-12


def test_no_correlated_term_means_no_change():
    lig = _lig()
    interactions = [
        FragmentInteraction("L0", "weak1", classical_term=-1.0, correlated_term=None),
        FragmentInteraction("L0", "metal", classical_term=2.0, correlated_term=None),
    ]
    s = rescore.build_score(lig, -7.0, -0.3, interactions)
    assert s.baseline_score == s.corrected_score
    assert s.delta == 0.0


def test_experimental_dg_passthrough():
    s = rescore.build_score(_lig(), -7.0, 0.0, [])
    assert s.experimental_dg == -9.0
