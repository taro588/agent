"""Safe, transactional Toolkit lifecycle operations."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, json, os, shutil, tempfile, time


@dataclass(frozen=True)
class InstallResult:
    ok: bool
    action: str
    root: str
    error: str | None = None
    version: str | None = None


class ToolkitInstaller:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.current = self.root / "current"
        self.versions = self.root / "versions"
        self.backups = self.root / "backups"
        self.state = self.root / "state.json"

    def _owned(self, path):
        target = Path(path).expanduser().resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Refusing to operate outside Toolkit root.") from exc
        return target

    def _manifest(self, directory):
        directory = self._owned(directory)
        files = {}
        for p in sorted(directory.rglob("*")):
            if p.is_file() and p.name != "manifest.json":
                files[str(p.relative_to(directory))] = hashlib.sha256(p.read_bytes()).hexdigest()
        return {"files": files}

    def _write_state(self, version):
        tmp = self.root / ".state.tmp"
        tmp.write_text(json.dumps({"current": version}, indent=2), encoding="utf-8")
        os.replace(tmp, self.state)

    def _read_current_version(self):
        try:
            return json.loads(self.state.read_text(encoding="utf-8")).get("current")
        except Exception:
            return None

    def install(self):
        try:
            for d in (self.current, self.versions, self.backups):
                d.mkdir(parents=True, exist_ok=True)
            return InstallResult(True, "install", str(self.root), version=self._read_current_version())
        except Exception as exc:
            return InstallResult(False, "install", str(self.root), f"{type(exc).__name__}: {exc}")

    def repair(self):
        r = self.install()
        return InstallResult(r.ok, "repair", r.root, r.error, r.version)

    def stage_update(self, source, version=None):
        try:
            source = Path(source).expanduser().resolve()
            if not source.is_dir():
                raise ValueError("Update source directory does not exist.")
            if source == self.root or self.root in source.parents:
                raise ValueError("Update source must not be inside the Toolkit root.")
            install_result = self.install()
            if not install_result.ok:
                raise RuntimeError(install_result.error or "Toolkit root could not be prepared.")
            version = version or time.strftime("%Y%m%d-%H%M%S")
            target = self._owned(self.versions / version)
            if target.exists():
                raise ValueError(f"Version already exists: {version}")
            try:
                shutil.copytree(source, target)
                (target / "manifest.json").write_text(
                    json.dumps(self._manifest(target), indent=2), encoding="utf-8"
                )
            except Exception:
                shutil.rmtree(target, ignore_errors=True)
                raise
            return InstallResult(True, "stage_update", str(self.root), version=version)
        except Exception as exc:
            return InstallResult(
                False, "stage_update", str(self.root),
                f"{type(exc).__name__}: {exc}", version
            )

    def _verify(self, target):
        try:
            data = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        except Exception as exc:
            return False, f"Invalid version manifest: {type(exc).__name__}: {exc}"
        files = data.get("files")
        if not isinstance(files, dict):
            return False, "Invalid version manifest: files must be an object."

        expected = set(files)
        actual = {
            str(p.relative_to(target))
            for p in target.rglob("*")
            if p.is_file() and p.name != "manifest.json"
        }
        unexpected = sorted(actual - expected)
        if unexpected:
            return False, f"Manifest contains unexpected files: {unexpected[0]}"

        for rel, digest in files.items():
            if not isinstance(rel, str) or Path(rel).is_absolute():
                return False, f"Invalid manifest path: {rel!r}"
            p = (target / rel).resolve()
            try:
                p.relative_to(target)
            except ValueError:
                return False, f"Invalid manifest path: {rel!r}"
            if not p.is_file():
                return False, f"Manifest file missing: {rel}"
            if not isinstance(digest, str):
                return False, f"Invalid checksum for: {rel}"
            if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                return False, f"Manifest checksum mismatch: {rel}"
        return True, None

    def _backup_current(self, version):
        """Move current aside and return its backup path, or None."""
        if not self.current.exists():
            return None
        backup_name = f"{version or 'unknown'}-{time.time_ns()}-previous"
        backup = self.backups / backup_name
        os.replace(self.current, backup)
        return backup

    def activate(self, version):
        staging = None
        old_current = None
        old_version = self._read_current_version()
        try:
            target = self._owned(self.versions / version)
            if not target.is_dir():
                raise ValueError(f"Version does not exist: {version}")
            ok, error = self._verify(target)
            if not ok:
                raise ValueError(error)
            staging = Path(tempfile.mkdtemp(prefix=".activate-", dir=self.root))
            staged_current = staging / "current"
            shutil.copytree(
                target, staged_current, ignore=shutil.ignore_patterns("manifest.json")
            )

            old_current = self._backup_current(old_version)
            os.replace(staged_current, self.current)
            try:
                self._write_state(version)
            except Exception:
                # State failure must not leave a new current version active.
                if self.current.exists():
                    failed_current = staging / "failed-current"
                    os.replace(self.current, failed_current)
                if old_current is not None and old_current.exists():
                    os.replace(old_current, self.current)
                raise

            return InstallResult(True, "activate", str(self.root), version=version)
        except Exception as exc:
            if old_current is not None and old_current.exists() and not self.current.exists():
                try:
                    os.replace(old_current, self.current)
                except OSError:
                    pass
            return InstallResult(
                False, "activate", str(self.root),
                f"{type(exc).__name__}: {exc}", version
            )
        finally:
            if staging:
                shutil.rmtree(staging, ignore_errors=True)

    def rollback(self, version=None):
        if version:
            return self.activate(version)

        old_version = self._read_current_version()
        backups = (
            [p for p in self.backups.iterdir() if p.is_dir()]
            if self.backups.exists() else []
        )
        if not backups:
            return InstallResult(False, "rollback", str(self.root), "No rollback backup is available.")

        # Backup names include the old version, so lexical ordering is not a
        # reliable proxy for recency. Filesystem mtime is the actual creation
        # order we control here.
        backup = max(backups, key=lambda p: p.stat().st_mtime_ns)
        previous = backup.name.rsplit("-previous", 1)[0]
        if previous == "unknown":
            previous = None

        staging = None
        try:
            staging = Path(tempfile.mkdtemp(prefix=".rollback-", dir=self.root))
            staged_current = staging / "current"
            os.replace(backup, staged_current)

            if self.current.exists():
                failed_current = staging / "failed-current"
                os.replace(self.current, failed_current)

            os.replace(staged_current, self.current)
            try:
                self._write_state(previous)
            except Exception:
                if self.current.exists():
                    os.replace(self.current, backup)
                failed_current = staging / "failed-current"
                if failed_current.exists():
                    os.replace(failed_current, self.current)
                raise

            return InstallResult(True, "rollback", str(self.root), version=previous)
        except Exception as exc:
            # If state update failed, the original current and backup are
            # restored above. Keep the recorded version untouched.
            return InstallResult(
                False, "rollback", str(self.root),
                f"{type(exc).__name__}: {exc}", old_version
            )
        finally:
            if staging:
                shutil.rmtree(staging, ignore_errors=True)

    def uninstall(self):
        try:
            if self.root.exists():
                shutil.rmtree(self.root)
            return InstallResult(True, "uninstall", str(self.root))
        except Exception as exc:
            return InstallResult(
                False, "uninstall", str(self.root),
                f"{type(exc).__name__}: {exc}"
            )
