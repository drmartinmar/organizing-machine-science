"""Execute analyst-written Python against a world's dataset in a subprocess.

The sandbox is a *containment* measure for cooperative agents, not a security
boundary against adversarial code: it runs the code in a scratch directory
containing only ``data.csv``, with a wall-clock timeout, no inherited
environment, ``python -I`` (isolated mode), and a preamble that blocks the
most common ways of touching the network or the filesystem.  Use a container
if you run untrusted models.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

PREAMBLE = r"""
import builtins as _b, sys as _sys
_BLOCKED = {"socket", "subprocess", "urllib", "requests", "http", "ftplib", "smtplib", "shutil", "ctypes",
            "multiprocessing", "pathlib", "glob", "importlib"}
_real_import = _b.__import__
def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    # Only police imports issued directly by the analyst's script (module __main__);
    # libraries may import whatever they need internally.
    if (globals or {}).get("__name__") == "__main__" and name.split(".")[0] in _BLOCKED:
        raise ImportError(f"import of {name} is not allowed in the analysis sandbox")
    return _real_import(name, globals, locals, fromlist, level)
_b.__import__ = _guarded_import
import warnings as _w
_w.filterwarnings("ignore")
import pandas as _pd
_pd.set_option("display.width", 160)
_pd.set_option("display.max_columns", 40)
_pd.set_option("display.max_rows", 120)
"""


@dataclass
class ExecResult:
    ok: bool
    stdout: str
    stderr: str
    seconds: float


def run_analysis(code: str, data_csv: Path, workdir: Path | None = None, timeout_s: int = 120,
                 max_output_chars: int = 6000) -> ExecResult:
    import time
    tmp = Path(tempfile.mkdtemp(prefix="oms-sbx-", dir=str(workdir) if workdir else None))
    try:
        shutil.copy(data_csv, tmp / "data.csv")
        script = tmp / "analysis.py"
        script.write_text(PREAMBLE + "\n" + code)
        env = {"PATH": os.environ.get("PATH", ""), "HOME": str(tmp), "PYTHONHASHSEED": "0",
               "MPLBACKEND": "Agg", "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2"}
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, "-I", str(script)], cwd=tmp, env=env, capture_output=True,
                               text=True, timeout=timeout_s)
            out, err, ok = p.stdout, p.stderr, p.returncode == 0
        except subprocess.TimeoutExpired as e:
            out, err, ok = (e.stdout or ""), f"TimeoutExpired after {timeout_s}s", False
            if isinstance(out, bytes):
                out = out.decode(errors="replace")
        secs = time.time() - t0
        if len(out) > max_output_chars:
            out = out[: max_output_chars // 2] + "\n...[output truncated]...\n" + out[-max_output_chars // 2:]
        if len(err) > 2500:
            err = err[-2500:]
        return ExecResult(ok=ok, stdout=out, stderr=err, seconds=round(secs, 2))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
