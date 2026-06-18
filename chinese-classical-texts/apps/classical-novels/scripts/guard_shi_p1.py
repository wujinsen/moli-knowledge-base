#!/usr/bin/env python3
"""Trust Guard · 诗词意象 P1：判词/曲子须含 inference 人物推论边。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_shi_p1.py"


def main() -> None:
    r = subprocess.run([sys.executable, str(AUDIT)], cwd=ROOT, check=False)
    raise SystemExit(r.returncode)


if __name__ == "__main__":
    main()
