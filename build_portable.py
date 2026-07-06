"""Build portable zip: include backend, frontend/dist (no node_modules), data (no db),
docs, start/stop scripts, env example, README, VERSION."""
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = "2026.07.03"
OUT = ROOT / f"repair-system-portable-v{VERSION}.zip"

# Items to include at top level (files or dirs)
INCLUDE_TOP = [
    "backend",
    "frontend",
    "data",
    "docs",
    "start.bat", "start.sh",
    "start_prod.bat", "start_prod.sh",
    "stop.bat", "stop.sh",
    ".env.example", ".gitignore",
    "README.md", "VERSION.txt",
]

# Exclusion patterns (relative paths or basename matches)
EXCLUDE_DIRS = {
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".git",
}
EXCLUDE_FRONTEND_DIRS = {"node_modules"}  # only exclude node_modules inside frontend/
EXCLUDE_FILES = {
    ".pyc", ".pyo", ".pyd",
    ".log", ".pid",
}
EXCLUDE_BASENAMES = {".DS_Store", "Thumbs.db"}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    is_under_frontend = "frontend" in parts
    for p in parts:
        if p in EXCLUDE_DIRS:
            return True
        if is_under_frontend and p in EXCLUDE_FRONTEND_DIRS:
            return True
        if p in EXCLUDE_BASENAMES:
            return True
    if path.is_file() and path.suffix.lower() in EXCLUDE_FILES:
        return True
    return False


def add_dir(zf: zipfile.ZipFile, src_dir: Path, arcname_prefix: str, keep_dir: bool = False):
    """Add all files under src_dir to zip under arcname_prefix."""
    if not src_dir.exists():
        print(f"  skip (missing): {src_dir.name}")
        return 0
    count = 0
    for p in sorted(src_dir.rglob("*")):
        if should_skip(p):
            continue
        if not p.is_file():
            continue
        rel = p.relative_to(src_dir)
        arcname = f"{arcname_prefix}/{rel.as_posix()}" if keep_dir else f"{arcname_prefix}/{rel.as_posix()}"
        zf.write(p, arcname)
        count += 1
    return count


def main():
    print(f"[build] writing {OUT.name}")
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for item in INCLUDE_TOP:
            src = ROOT / item
            if not src.exists():
                print(f"  skip (missing): {item}")
                continue
            if src.is_file():
                if should_skip(src):
                    continue
                zf.write(src, item)
                print(f"  + file: {item}")
            else:
                n = add_dir(zf, src, item)
                print(f"  + dir : {item} ({n} files)")
    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"[build] done: {OUT.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()