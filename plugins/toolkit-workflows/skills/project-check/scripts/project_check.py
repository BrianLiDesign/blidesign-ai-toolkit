#!/usr/bin/env python3
"""Discover project checks without execution, or run an explicit reviewed manifest.

Python standard library only. No shell, package installation, or automatic retries.
Commands execute with the caller's permissions; this is not a sandbox.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


OUTPUT_LIMIT = 32768
CATEGORIES = {"build", "lint", "typecheck", "test", "security", "acceptance"}
IDENTIFIER = re.compile(r"^[a-zA-Z0-9_-]+$")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def within(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Manifest paths must remain within the project")
    return path


def validate_plan(root, data):
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("Manifest requires schemaVersion 1")
    if set(data) - {"schemaVersion", "checks", "requiredCategories"}:
        raise ValueError("Unsupported manifest fields")
    required = data.get("requiredCategories", ["test"])
    if not isinstance(required, list) or not required or any(c not in CATEGORIES for c in required):
        raise ValueError("requiredCategories must name at least one supported category")
    checks = data.get("checks")
    if not isinstance(checks, list):
        raise ValueError("checks must be a list")
    seen = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) - {"id", "category", "argv", "cwd", "timeoutSeconds", "required"}:
            raise ValueError("Unsupported check definition")
        name = check.get("id")
        if not isinstance(name, str) or not IDENTIFIER.fullmatch(name) or name in seen:
            raise ValueError("Check identifiers must be unique names")
        seen.add(name)
        if check.get("category") not in CATEGORIES:
            raise ValueError(f"{name}: unsupported category")
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) and "\0" not in a for a in argv) or not argv[0]:
            raise ValueError(f"{name}: argv must be a nonempty list of strings")
        timeout = check.get("timeoutSeconds", 120)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 86400:
            raise ValueError(f"{name}: timeoutSeconds must be positive and at most 86400")
        if not isinstance(check.get("required", True), bool):
            raise ValueError(f"{name}: required must be boolean")
        if not isinstance(check.get("cwd", "."), str) or not within(root, check.get("cwd", ".")).is_dir():
            raise ValueError(f"{name}: cwd must be a project directory")
    return checks, required


def discover(root):
    """Return reviewable candidates; never execute package scripts or documentation."""
    candidates = []
    if (root / "package.json").is_file():
        scripts = read_json(root / "package.json").get("scripts", {})
        manager = next((m for lock, m in [("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("package-lock.json", "npm")] if (root / lock).exists()), None)
        for name in scripts:
            category = next((c for prefix, c in [("build", "build"), ("lint", "lint"), ("typecheck", "typecheck"), ("type-check", "typecheck"), ("test", "test")] if name == prefix or name.startswith(prefix + ":")), None)
            if category:
                candidates.append({"id": name, "category": category, "argv": [manager, "run", name] if manager else None, "source": f"package.json#scripts.{name}", "needsReview": True})
    if (root / "tests").is_dir() and any((root / "tests").glob("test*.py")):
        candidates.append({"id": "python-unittest", "category": "test", "argv": ["{python}", "-m", "unittest", "discover", "-s", "tests", "-v"], "source": "tests/test*.py", "needsReview": True})
    documents = [name for name in ["AGENTS.md", "CONTRIBUTING.md", "README.md", "pyproject.toml", "Makefile", "justfile"] if (root / name).is_file()]
    documents += [p.relative_to(root).as_posix() for p in sorted((root / ".github/workflows").glob("*.y*ml"))]
    return {"mode": "discovery", "executed": False, "manifestPresent": (root / ".project-check.json").exists(), "candidates": candidates, "reviewSources": documents}


def redactor(extra_names):
    names = [name for name in os.environ if re.search(r"TOKEN|SECRET|PASSWORD|CREDENTIAL|(?:^|_)KEY(?:$|_)", name, re.I)]
    values = sorted({os.environ[name] for name in [*names, *extra_names] if len(os.environ.get(name, "")) >= 4}, key=len, reverse=True)

    def redact(text):
        for value in values:
            text = text.replace(value, "<REDACTED>")
        text = re.sub(r"gh[oprsu]_\w{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}", "<REDACTED>", text)
        text = re.sub(r"(?i)(authorization\s*[:=]\s*(?:bearer\s+|basic\s+)?)[^\s\"']+", r"\1<REDACTED>", text)
        return text

    return redact


def git_state(root):
    def git(*args):
        try:
            result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=5)
            return result.stdout if result.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            return None
    commit_output = git("rev-parse", "HEAD")
    commit = commit_output.strip() if commit_output else None
    state = git("status", "--porcelain", "--", ".") if commit else None
    fingerprint = None
    if commit:
        diff = git("diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD", "--", ".")
        untracked = git("ls-files", "--others", "--exclude-standard", "-z")
        if diff is not None and untracked is not None and state is not None:
            hasher = hashlib.sha256((state + "\0" + diff).encode("utf-8"))
            try:
                for name in sorted(filter(None, untracked.split("\0"))):
                    path = root / name
                    hasher.update(name.encode("utf-8"))
                    if path.is_symlink():
                        hasher.update(os.readlink(path).encode("utf-8"))
                    else:
                        with path.open("rb") as stream:
                            while chunk := stream.read(65536):
                                hasher.update(chunk)
                fingerprint = hasher.hexdigest()
            except OSError:
                pass
    return {"commit": commit, "dirty": bool(state) if state is not None else None, "sourceFingerprint": fingerprint}


def stop_process(process):
    if os.name == "nt":
        result = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=10)
        if result.returncode and process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=10)


def execute(root, check, redact):
    argv = [sys.executable if arg == "{python}" else arg for arg in check["argv"]]
    command = shutil.which(argv[0]) or argv[0]
    # Windows cannot reliably spawn npm/pnpm command shims directly. Use their
    # Node entrypoints, preserving argv boundaries without invoking cmd.exe.
    if os.name == "nt" and Path(command).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        base = Path(command).parent
        entry = {"npm": base / "node_modules/npm/bin/npm-cli.js", "pnpm": base / "node_modules/pnpm/bin/pnpm.cjs", "yarn": base / "node_modules/yarn/bin/yarn.js"}.get(Path(command).stem.lower())
        if entry is None or not entry.is_file():
            return {"status": "error", "exitCode": None, "durationSeconds": 0, "stdout": "", "stderr": "Use an executable or explicit interpreter instead of a Windows shell shim"}
        argv = [shutil.which("node") or "node", str(entry), *argv[1:]]
    else:
        argv[0] = command
    started = time.monotonic()
    buffers = [bytearray(), bytearray()]
    truncated = [False, False]
    process = None
    readers = []
    status, code, error = "error", None, ""

    def read(stream, index):
        while chunk := stream.read(4096):
            buffers[index].extend(chunk)
            if len(buffers[index]) > OUTPUT_LIMIT:
                truncated[index] = True
                del buffers[index][:-OUTPUT_LIMIT]

    try:
        process = subprocess.Popen(argv, cwd=within(root, check.get("cwd", ".")), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=os.name != "nt", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for index, stream in enumerate([process.stdout, process.stderr]):
            thread = threading.Thread(target=read, args=(stream, index), daemon=True)
            thread.start()
            readers.append(thread)
        try:
            code = process.wait(timeout=check.get("timeoutSeconds", 120))
            status = "passed" if code == 0 else "failed"
        except subprocess.TimeoutExpired:
            status = "timeout"
            stop_process(process)
            code = process.returncode
        except KeyboardInterrupt:
            stop_process(process)
            raise
    except (OSError, subprocess.SubprocessError) as exception:
        error = str(exception)
    finally:
        for thread in readers:
            thread.join(timeout=2)
        if any(thread.is_alive() for thread in readers):
            status, error = "error", "A descendant retained an output pipe; output is incomplete"
    # Drop a truncated leading line so a clipped credential is not emitted as a
    # partial value which the full-value redactor can no longer recognize.
    output = [bytes(buf).split(b"\n", 1)[-1] if cut and b"\n" in buf else b"" if cut else bytes(buf) for buf, cut in zip(buffers, truncated)]
    return {"status": status, "exitCode": code, "durationSeconds": round(time.monotonic() - started, 3), "stdout": redact(output[0].decode("utf-8", errors="replace")), "stderr": redact(output[1].decode("utf-8", errors="replace") + error), "outputTruncated": any(truncated)}


def run_plan(root, checks, required, selected, redact):
    unknown = set(selected) - {check["id"] for check in checks}
    if unknown:
        raise ValueError("Unknown check selection: " + ", ".join(sorted(unknown)))
    before = git_state(root)
    report = {"schemaVersion": 1, "mode": "execution", "startedAt": datetime.now(timezone.utc).isoformat(), "git": before, "checks": []}
    for check in checks:
        result = {"id": check["id"], "category": check["category"], "required": check.get("required", True), "argv": [redact(a) for a in check["argv"]], "cwd": check.get("cwd", "."), "timeoutSeconds": check.get("timeoutSeconds", 120)}
        result.update(execute(root, check, redact) if not selected or check["id"] in selected else {"status": "not_run"})
        report["checks"].append(result)
    after = git_state(root)
    report["gitAfter"] = after
    report["changedDuringRun"] = before != after
    passed = {c["category"] for c in report["checks"] if c["status"] == "passed"}
    report["missingCategories"] = sorted(set(required) - passed)
    failed = any(c["status"] in {"failed", "timeout", "error"} for c in report["checks"])
    partial = bool(report["missingCategories"]) or any(c["required"] and c["status"] == "not_run" for c in report["checks"]) or bool(before["commit"] and not before["sourceFingerprint"])
    report["status"] = "failed" if failed else "partial" if partial or report["changedDuringRun"] else "passed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--discover", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--manifest", default=".project-check.json")
    parser.add_argument("--check", action="append", default=[])
    parser.add_argument("--report", type=Path)
    parser.add_argument("--redact-env", action="append", default=[])
    args = parser.parse_args()
    redact = redactor(args.redact_env)
    try:
        root = args.root.expanduser().resolve()
        if not root.is_dir():
            raise ValueError("Project root must be a directory")
        if args.check and not args.run:
            raise ValueError("--check requires --run")
        manifest = within(root, args.manifest)
        if args.report:
            output = args.report.expanduser().resolve()
            if output == manifest or output.is_relative_to(Path(__file__).resolve().parent):
                raise ValueError("Report must not overwrite the manifest or runner")
            if output.is_relative_to(root):
                raise ValueError("Store reports outside the project to keep evidence out of source control")
        if args.run:
            checks, required = validate_plan(root, read_json(manifest))
            report = run_plan(root, checks, required, args.check, redact)
        else:
            report = discover(root)
        text = redact(json.dumps(report, indent=2)) + "\n"
        if args.report:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
        print(text, end="")
        return {"passed": 0, "failed": 1, "partial": 2}.get(report.get("status"), 0)
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({"status": "error", "error": redact(str(error))}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
