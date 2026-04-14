#!/usr/bin/env python3
"""Validate changelog and version metadata consistency."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "changelog" / "CHANGELOG.md"
VERSIONED_FILE = re.compile(r"_v(?P<version>\d+)\.(?P<ext>ya?ml|json|md)$")
CHANGELOG_HEADING = re.compile(r"^##\s+(\d+)\.(\d+)\.(\d+)\s*$")


def git_tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line.strip() for line in result.stdout.splitlines() if line.strip()]


def parse_changelog_versions() -> list[tuple[int, int, int]]:
    versions: list[tuple[int, int, int]] = []
    with CHANGELOG.open("r", encoding="utf-8") as f:
        for line in f:
            match = CHANGELOG_HEADING.match(line.strip())
            if match:
                versions.append(tuple(int(part) for part in match.groups()))

    if not versions:
        raise ValueError("changelog/CHANGELOG.md must contain at least one '## x.y.z' release heading")

    if len(versions) != len(set(versions)):
        raise ValueError("changelog/CHANGELOG.md contains duplicate release headings")

    return versions


def yaml_top_level_version(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        if re.match(r"^version\s*:", line):
            return line.split(":", 1)[1].strip().strip("\"'")
        # only inspect top-level preamble before nested content starts
        if line.startswith((" ", "\t")):
            continue
    return None


def validate_file_versions() -> int:
    checked = 0
    for path in git_tracked_files():
        rel = path.relative_to(ROOT)
        match = VERSIONED_FILE.search(path.name)
        if not match:
            continue

        checked += 1
        expected_major = int(match.group("version"))
        ext = match.group("ext")

        if ext in {"yaml", "yml"}:
            declared = yaml_top_level_version(path)
            if declared is None:
                continue
            v_match = re.fullmatch(r"v(\d+)", declared)
            if v_match:
                major = int(v_match.group(1))
            else:
                semver = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", declared)
                if not semver:
                    raise ValueError(f"{rel}: version must be 'vN' or 'N.N.N', got '{declared}'")
                major = int(semver.group(1))

            if major != expected_major:
                raise ValueError(
                    f"{rel}: filename expects major version {expected_major}, but version field is '{declared}'"
                )

        if ext == "json":
            # Ensure versioned JSON files are syntactically valid.
            json.loads(path.read_text(encoding="utf-8"))

    return checked


def main() -> int:
    releases = parse_changelog_versions()
    checked = validate_file_versions()
    latest = max(releases)
    print(f"validated changelog releases: {len(releases)} (latest: {latest[0]}.{latest[1]}.{latest[2]})")
    print(f"validated versioned files: {checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
