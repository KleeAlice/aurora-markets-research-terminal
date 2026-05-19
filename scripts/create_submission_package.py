from __future__ import annotations

import shutil
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_DIR = ROOT / "submission"
STAGING_DIR = SUBMISSION_DIR / "staging"
ZIP_PATH = SUBMISSION_DIR / "aurora-markets-research-terminal-submission.zip"
REPORTS_DIR = STAGING_DIR / "reports"

API_DIR = ROOT / "apps" / "api"
WEB_DIR = ROOT / "apps" / "web"


def reset_output() -> None:
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    SUBMISSION_DIR.mkdir(exist_ok=True)
    STAGING_DIR.mkdir(parents=True)


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            ".pytest_cache",
            ".venv",
            "node_modules",
            "dist",
            ".env",
            ".env.*",
            "*.pyc",
            ".vite-*.log",
            ".tmp-*.png",
        ),
    )


def copy_project_files() -> None:
    for name in ["app.py", "README.md", "docker-compose.yml", "AGENTS.md", ".gitignore"]:
        path = ROOT / name
        if path.exists():
            copy_file(path, STAGING_DIR / name)

    guide_path = ROOT / "docs" / "SUBMISSION_GUIDE.md"
    if not guide_path.exists():
        guide_path = ROOT / "SUBMISSION_GUIDE.md"
    copy_file(guide_path, STAGING_DIR / "SUBMISSION_GUIDE.md")

    api_target = STAGING_DIR / "apps" / "api"
    copy_file(API_DIR / "requirements.txt", api_target / "requirements.txt")
    copy_file(API_DIR / "Dockerfile", api_target / "Dockerfile")
    copy_tree(API_DIR / "new_energy_broker", api_target / "new_energy_broker")
    copy_tree(API_DIR / "tests", api_target / "tests")

    web_target = STAGING_DIR / "apps" / "web"
    for name in ["Dockerfile", "index.html", "package.json", "package-lock.json", "tsconfig.json", "vite.config.ts"]:
        path = WEB_DIR / name
        if path.exists():
            copy_file(path, web_target / name)
    copy_tree(WEB_DIR / "src", web_target / "src")

    scripts_target = STAGING_DIR / "scripts"
    copy_file(ROOT / "scripts" / "create_submission_package.py", scripts_target / "create_submission_package.py")


def write_report_bundle() -> None:
    sys.path.insert(0, str(API_DIR))
    from new_energy_broker.services import build_report, minimal_pdf_bytes

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_specs = [
        ("002594.SZ", "BYD_002594_SZ"),
        ("TSLA", "TSLA"),
    ]
    for ticker, filename in report_specs:
        report = build_report(ticker)
        (REPORTS_DIR / f"{filename}.md").write_text(report.markdown, encoding="utf-8")
        (REPORTS_DIR / f"{filename}.html").write_text(
            "<!doctype html><html><head><meta charset='utf-8'><title>"
            + report.title
            + "</title></head><body>"
            + report.html
            + "</body></html>",
            encoding="utf-8",
        )
        (REPORTS_DIR / f"{filename}.pdf").write_bytes(minimal_pdf_bytes(report))


def write_manifest() -> None:
    files = []
    for path in sorted(STAGING_DIR.rglob("*")):
        if path.is_file():
            files.append(f"- {path.relative_to(STAGING_DIR).as_posix()} ({path.stat().st_size} bytes)")
    manifest = [
        "# Submission Manifest",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Privacy exclusions applied: .runtime, apps/runtime_assets, node_modules, dist, .venv, __pycache__, .pytest_cache, .env*, local API config, browser profile/cache, smoke logs/screenshots.",
        "",
        "## Files",
        *files,
        "",
    ]
    (STAGING_DIR / "MANIFEST.md").write_text("\n".join(manifest), encoding="utf-8")


def assert_clean() -> None:
    banned_parts = {
        ".runtime",
        "runtime_assets",
        "node_modules",
        "dist",
        ".venv",
        "__pycache__",
        ".pytest_cache",
    }
    banned_names = {"api_config.json"}
    banned_text = ["aurora" + "-user-profile", "David" + " Chen"]
    key_pattern = re.compile(r"\b(?:sk|sk-ant|gsk)_[A-Za-z0-9_-]{8,}|\bsk-[A-Za-z0-9_-]{8,}")
    for path in STAGING_DIR.rglob("*"):
        rel_parts = set(path.relative_to(STAGING_DIR).parts)
        if banned_parts & rel_parts:
            raise RuntimeError(f"Forbidden path included: {path}")
        if path.name in banned_names:
            raise RuntimeError(f"Forbidden file included: {path}")
        if path.is_file() and path.suffix.lower() in {".py", ".ts", ".vue", ".md", ".json", ".html", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for needle in banned_text:
                if needle in text:
                    raise RuntimeError(f"Forbidden text {needle!r} found in {path}")
            if key_pattern.search(text):
                raise RuntimeError(f"Possible API key found in {path}")


def make_zip() -> None:
    with ZipFile(ZIP_PATH, "w", ZIP_DEFLATED) as archive:
        for path in sorted(STAGING_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(STAGING_DIR))


def main() -> None:
    reset_output()
    copy_project_files()
    write_report_bundle()
    write_manifest()
    assert_clean()
    make_zip()
    print(f"Created {ZIP_PATH}")
    print(f"Staging directory: {STAGING_DIR}")


if __name__ == "__main__":
    main()
