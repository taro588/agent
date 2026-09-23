from __future__ import annotations

import base64
import json
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "2.1.7"
CHECKOUT_V7_0_1 = "3d3c42e5aac5ba805825da76410c181273ba90b1"
ATTEST_V4_2_2 = "1e69f48acb82d1966a394da916b4c1698aa569d6"
ACTIONLINT_V1_7_12 = "914e7df21a07ef503a81201c76d2b11c789d3fca"
EXPECTED_RELEASE_FILES = [
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "README.txt",
    "SECURITY.md",
    "SUPPORT.md",
    "VERSION",
    "Windows双击安装Codex.cmd",
    "Windows双击更新Codex.cmd",
    "docs/configuration.md",
    "docs/migration-v2.md",
    "docs/troubleshooting.md",
    "install-codex-linux.sh",
    "install-codex-macos.sh",
    "install-codex-unix.sh",
    "install-codex.ps1",
    "macOS双击安装Codex.command",
    "macOS双击更新Codex.command",
]
INSTALLER_SOURCES = [
    "install-codex-linux.sh",
    "install-codex-macos.sh",
    "install-codex.ps1",
    "install-codex-unix.sh",
]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def repository_files() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [
        ROOT / raw.decode("utf-8")
        for raw in result.stdout.split(b"\0")
        if raw
    ]


class RepositoryContractTests(unittest.TestCase):
    def test_version_is_stable_semver(self) -> None:
        version = read("VERSION").strip()
        self.assertEqual(version, EXPECTED_VERSION)
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        for relative in INSTALLER_SOURCES:
            self.assertNotIn(
                EXPECTED_VERSION,
                read(relative),
                f"{relative} must not embed the repository release version",
            )

    def test_release_manifest_is_explicit_sorted_and_complete(self) -> None:
        manifest = [
            line.strip()
            for line in read("scripts/release-files.txt").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(manifest, sorted(manifest))
        self.assertEqual(manifest, EXPECTED_RELEASE_FILES)
