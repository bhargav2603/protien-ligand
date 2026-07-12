"""IBM Quantum: async submit/retrieve and the noise-cancellation integrity check.

Colab disconnects; hardware queues outlive sessions. So submit saves a job_id
and returns immediately; retrieve reads it back later. Never block on a job.
"""
from __future__ import annotations

from ..runtime import Context


def get_service(ctx: Context):
    """A QiskitRuntimeService, or None if no credentials are configured."""
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService()
        ctx.log(f"IBM backends: {[b.name for b in service.backends()]}")
        return service
    except Exception as e:
        ctx.decide("IBM hardware", "unavailable",
                   f"no runtime credentials ({str(e)[:100]}); simulation path only")
        return None


def _transpile(ctx: Context, circuit, backend):
    try:
        import ffsim
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
        pm.pre_init = ffsim.qiskit.PRE_INIT
        return pm.run(circuit)
    except Exception as e:
        ctx.log(f"ffsim PRE_INIT unavailable ({str(e)[:80]}); plain transpile", "WARNING")
        from qiskit import transpile
        return transpile(circuit, backend, optimization_level=3)


def submit(ctx: Context, service, circuit, shots: int, min_qubits: int,
           job_tag: str = "cpd1") -> str:
    """Transpile + submit; persist job_id to Drive; return it. Safe to disconnect."""
    from qiskit_ibm_runtime import SamplerV2

    backend = service.least_busy(operational=True, simulator=False,
                                 min_num_qubits=min_qubits)
    ctx.log(f"least-busy backend: {backend.name} ({backend.num_qubits} qubits)")
    isa = _transpile(ctx, circuit, backend)
    job = SamplerV2(mode=backend).run([isa], shots=shots)
    jid = job.job_id()
    (ctx.settings.checkpoints / f"job_id_{job_tag}.txt").write_text(jid, encoding="utf-8")
    ctx.decide("hardware submission", jid,
               f"async submit to {backend.name}; retrieve in a later session")
    return jid


def retrieve(ctx: Context, service, job_tag: str = "cpd1"):
    """Return a BitArray if the saved job is done, else None (do not block)."""
    path = ctx.settings.checkpoints / f"job_id_{job_tag}.txt"
    if not path.exists():
        return None
    jid = path.read_text(encoding="utf-8").strip()
    job = service.job(jid)
    ctx.log(f"job {jid} status = {job.status()}")
    if not job.done():
        ctx.log("job not finished; exit cleanly and retrieve later.", "INFO")
        return None
    bit_array = job.result()[0].data.meas
    ctx.save(f"{job_tag}_hw_bitarray", bit_array)
    return bit_array


def integrity_check(ctx: Context, e_hardware: float, e_noiseless: float,
                    tol: float = 1e-6) -> bool:
    """Noise-cancellation trap. Hardware below the noiseless reference is an
    artefact, never a win. Returns True if the result is CLEAN.
    """
    if e_hardware < e_noiseless - tol:
        ctx.log("RED FLAG: hardware energy BELOW the noiseless reference -- "
                "noise-induced error cancellation (cf. Kirsopp 2022), NOT advantage. "
                "Do not report as a win.", "CRITICAL")
        ctx.decide("integrity check", "FAILED (noise-cancellation)",
                   f"E_hw={e_hardware:.6f} < E_noiseless={e_noiseless:.6f}")
        return False
    ctx.log(f"integrity check clean: E_hw={e_hardware:.6f} >= "
            f"E_noiseless={e_noiseless:.6f}")
    return True
