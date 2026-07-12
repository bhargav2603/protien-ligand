"""Pipeline control-flow exceptions."""
from __future__ import annotations


class GateFailure(RuntimeError):
    """A hard gate / kill-criterion tripped: HALT this stage.

    Raised for the conditions in the kill-criteria table (SQD != CASCI, DFT
    functionals agree, active space below the 40-qubit wall, ...). The CLI
    catches it, logs it, and still emits a partial report.
    """
