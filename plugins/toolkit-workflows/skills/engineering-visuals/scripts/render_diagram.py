#!/usr/bin/env python3
"""Render with an installed local tool; preserve source and publish only successful output."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "assets/mermaid-config.json"


def executable_path(value: str) -> str:
    resolved = shutil.which(value)
    if not resolved:
        raise ValueError(f"Local executable unavailable: {value}. No dependencies were installed.")
    if Path(resolved).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        raise ValueError("Use a native executable; for Mermaid use node with --mermaid-cli.")
    return str(Path(resolved).resolve())


def existing_file(value: Path) -> Path:
    resolved = value.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"Expected a file: {value}")
    return resolved


def command(args: argparse.Namespace, source: Path, output: Path) -> list[str]:
    defaults = {"mermaid": "node", "graphviz": "dot", "drawio": "drawio"}
    executable = executable_path(args.executable or defaults[args.engine])
    if args.engine == "mermaid":
        if args.mermaid_cli is None:
            raise ValueError("Mermaid requires --mermaid-cli pointing to the installed src/cli.js.")
        cli = existing_file(args.mermaid_cli)
        config = existing_file(args.config or DEFAULT_CONFIG)
        argv = [executable, str(cli), "-i", str(source), "-o", str(output), "-c", str(config)]
        if args.puppeteer_config:
            argv.extend(["-p", str(existing_file(args.puppeteer_config))])
        return argv
    if args.mermaid_cli or args.config or args.puppeteer_config:
        raise ValueError("Mermaid configuration options apply only to the mermaid engine.")
    if args.engine == "graphviz":
        return [executable, f"-T{output.suffix[1:]}", str(source), "-o", str(output)]
    return [executable, "--disable-update", "--export", "--format", output.suffix[1:],
            "--page-index", str(args.page_index), "--output", str(output), str(source)]


def run_renderer(argv: list[str], timeout: float, cwd: Path) -> None:
    # Separate process group permits cleanup of browser children after a timeout.
    options = {"start_new_session": True} if os.name != "nt" else {
        "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    }
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(argv, cwd=cwd, stdout=log, stderr=log, shell=False, **options)
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/taskkill.exe"
                subprocess.run([str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                os.killpg(process.pid, signal.SIGKILL)
            if process.poll() is None:
                process.kill()
            process.wait()
            raise ValueError(f"Renderer timed out after {timeout:g} seconds.") from None
        if returncode:
            log.seek(0)
            detail = log.read(2000).decode("utf-8", errors="replace").strip()
            raise ValueError(f"Renderer failed ({returncode}): {detail}")


def check_output(output: Path) -> None:
    if not output.is_file() or not output.stat().st_size:
        raise ValueError("Renderer produced no nonempty output.")
    with output.open("rb") as handle:
        header = handle.read(8)
    if output.suffix == ".svg":
        if ET.parse(output).getroot().tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError("Renderer output is not an SVG document.")
    elif output.suffix == ".png" and header != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Renderer output has no PNG signature.")
    elif output.suffix == ".pdf" and not header.startswith(b"%PDF-"):
        raise ValueError("Renderer output has no PDF signature.")


def render(args: argparse.Namespace) -> dict[str, str]:
    if args.timeout <= 0 or not args.timeout < float("inf"):
        raise ValueError("Timeout must be finite and positive.")
    if args.page_index < 0 or (args.page_index != 0 and args.engine != "drawio"):
        raise ValueError("A nonnegative page index is supported only for drawio.")
    source = existing_file(args.input)
    raw_output = args.output.absolute()
    if raw_output.is_symlink():
        raise ValueError("Output must not be a symbolic link.")
    output = raw_output.resolve()
    protected = [source, *(existing_file(value) for value in
                 [args.mermaid_cli, args.config, args.puppeteer_config] if value)]
    if any(output == value or (output.exists() and output.samefile(value)) for value in protected):
        raise ValueError("Output must differ from source, renderer entrypoint, and configuration.")
    if output.suffix not in {".svg", ".png", ".pdf"}:
        raise ValueError("Output extension must be .svg, .png, or .pdf.")
    if output.exists() and (not output.is_file() or not args.overwrite):
        raise ValueError("Output already exists; choose a new path or explicitly use --overwrite.")
    # Resolve tooling before creating directories or running anything.
    command(args, source, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".diagram-", dir=output.parent) as directory:
        staged = Path(directory) / output.name
        run_renderer(command(args, source, staged), args.timeout, source.parent)
        check_output(staged)
        if args.overwrite:
            os.replace(staged, output)
        else:
            # Exclusive create also protects against an output appearing during rendering.
            with output.open("xb") as destination, staged.open("rb") as generated:
                shutil.copyfileobj(generated, destination)
    return {"status": "rendered", "engine": args.engine, "source": str(source),
            "output": str(output), "domainCheck": "not-performed", "visualInspection": "not-performed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=["mermaid", "graphviz", "drawio"], required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executable", help="Trusted local native executable; defaults to node/dot/drawio")
    parser.add_argument("--mermaid-cli", type=Path, help="Installed Mermaid src/cli.js entrypoint")
    parser.add_argument("--config", type=Path, help="Reviewed Mermaid JSON configuration")
    parser.add_argument("--puppeteer-config", type=Path, help="Reviewed browser launch configuration")
    parser.add_argument("--page-index", type=int, default=0, help="Zero-based draw.io page index")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing export after success")
    args = parser.parse_args()
    try:
        print(json.dumps(render(args)))
        return 0
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"Render failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
