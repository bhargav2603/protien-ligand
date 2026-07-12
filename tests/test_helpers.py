"""Pure-logic helpers: electron/spin splitting and settings."""
import pytest

from qadv.chem.active_space import split_nelec
from qadv.settings import Settings


@pytest.mark.parametrize("total,spin,expected", [
    (8, 4, (6, 2)),     # FeP quintet active space
    (10, 0, (5, 5)),    # closed shell
    (7, 1, (4, 3)),     # doublet
])
def test_split_nelec(total, spin, expected):
    assert split_nelec(total, spin) == expected


def test_split_nelec_parity_guard():
    with pytest.raises(ValueError):
        split_nelec(8, 3)   # 8 electrons cannot have odd spin


def test_settings_paths(tmp_path):
    s = Settings.from_env(tmp_path)
    assert s.checkpoints == tmp_path / "checkpoints"
    assert s.decisions_file == tmp_path / "DECISIONS.md"
    assert s.basis == "cc-pvdz"


def test_settings_overrides(tmp_path):
    s = Settings.from_env(tmp_path, basis="def2-SVP", seed=7)
    assert s.basis == "def2-SVP"
    assert s.seed == 7
