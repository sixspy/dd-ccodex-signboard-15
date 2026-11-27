"""统计业务源码行数（不含 vendor / tests / Docker / README）。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {"node_modules", "__pycache__", ".pytest_cache", "tests", "scripts", ".git", "data"}
SKIP_NAMES = {"vue.global.prod.js", "README.md", "Dockerfile"}


def main() -> None:
    total = 0
    by: dict[str, int] = {}
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if set(p.relative_to(ROOT).parts) & SKIP_PARTS:
            continue
        if p.name in SKIP_NAMES or p.suffix == ".md" or p.name.startswith("_build"):
            continue
        if p.suffix in {".py", ".js", ".html", ".css"} or (p.suffix == ".json" and "fixtures" in p.parts):
            n = len(p.read_text(encoding="utf-8").splitlines())
            total += n
            by[p.suffix] = by.get(p.suffix, 0) + n
    print("业务 LOC 合计:", total)
    for k, v in sorted(by.items()):
        print(f"  {k}: {v}")
    print("达标:" if total >= 3000 else "未达标（须 >= 3000）", total >= 3000)


if __name__ == "__main__":
    main()
