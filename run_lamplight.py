"""Launch the Godot game and its private local Python service.

python run_lamplight.py --setup   # download the pinned portable engine
python run_lamplight.py           # play
python run_lamplight.py --editor  # edit the project; F6/F5 uses this service
python run_lamplight.py --check   # headless engine check with temporary saves
python run_lamplight.py --hyper   # preload HyperCharm; qualify inside the game
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import pathlib
import shutil
import subprocess
import tempfile
import threading
import zipfile
from http.server import ThreadingHTTPServer

import game_native
import game_server

ROOT = pathlib.Path(__file__).resolve().parent
VERSION = "4.7.2-stable"
ENGINE_DIR = ROOT / ".cache" / "godot"
ENGINE = ENGINE_DIR / f"Godot_v{VERSION}_win64_console.exe"


@contextlib.contextmanager
def single_library(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "service.lock").open("a+b") as guard:
        if guard.tell() == 0:
            guard.write(b" ")
            guard.flush()
        guard.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit("This native library is already open. Use the running game/editor before starting another.") from None
        yield  # Closing the handle releases the OS lock, including after a crash.


def setup():
    if os.name != "nt":
        raise SystemExit("Install Godot 4 for your platform and use --godot PATH.")
    name = f"Godot_v{VERSION}_win64.exe.zip"
    base = f"https://github.com/godotengine/godot-builds/releases/download/{VERSION}/"
    response = game_server.requests.get(base + "SHA512-SUMS.txt", timeout=30)
    response.raise_for_status()
    hashes = {line.split()[-1].lstrip("*"): line.split()[0] for line in response.text.splitlines() if line.strip()}
    expected = hashes[name]
    ENGINE_DIR.mkdir(parents=True, exist_ok=True)
    archive = ENGINE_DIR / (name + ".part")
    digest = hashlib.sha512()
    with game_server.requests.get(base + name, stream=True, timeout=(15, 90)) as download:
        download.raise_for_status()
        with archive.open("wb") as output:
            size = 0
            for chunk in download.iter_content(1024 * 1024):
                size += len(chunk)
                if size > 200_000_000:
                    raise ValueError("Engine download exceeds the expected size limit")
                digest.update(chunk)
                output.write(chunk)
    if digest.hexdigest() != expected:
        raise ValueError("Engine checksum mismatch; the downloaded file was not executed")
    with zipfile.ZipFile(archive) as bundle:
        for filename in (ENGINE.name, f"Godot_v{VERSION}_win64.exe"):
            entry = bundle.getinfo(filename)
            if entry.file_size > 300_000_000:
                raise ValueError("Unexpected engine archive size")
            with bundle.open(entry) as source, (ENGINE_DIR / filename).open("wb") as target:
                shutil.copyfileobj(source, target)
    archive.unlink()
    (ENGINE_DIR / "_sc_").touch()
    print(f"Verified portable Godot {VERSION}: {ENGINE}")


def setup_hyper(library):
    key = os.environ.get("AW_API_KEY", "")
    if not key:
        raise ValueError("Set AW_API_KEY in .env for HyperCharm setup")
    library.request(dict(op="ai_config", url=os.environ.get("AW_BASE_URL", "https://hyper.charm.land/v1"),
                         model="qwen3.8-max", key=key, enabled=True))
    print("HyperCharm loaded. Open AI setup in the game to connect and benchmark.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", action="store_true")
    parser.add_argument("--hyper", action=argparse.BooleanOptionalAction,
                        default=os.environ.get("LAMPLIGHT_AUTO_HYPER") == "1",
                        help="Preload Qwen Max using the existing HyperCharm key; no startup API calls")
    parser.add_argument("--godot", default=str(ENGINE) if ENGINE.exists() else shutil.which("godot") or shutil.which("godot4"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--editor", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--capture", action="store_true", help="Render native review screenshots using temporary saves")
    args = parser.parse_args()
    if args.setup:
        setup()
        return
    if not args.godot:
        raise SystemExit("Godot is missing. Run python run_lamplight.py --setup, or pass --godot PATH.")
    if pathlib.Path(args.godot).resolve().parent == ENGINE_DIR.resolve():
        (ENGINE_DIR / "_sc_").touch()  # Keep this portable editor's caches inside the project.
    game_server.BOOKS = game_native.campaign.BOOKS | {
        b["id"]: b for b in game_server.read_json(game_server.WEB / "books.json", [])}
    with tempfile.TemporaryDirectory(prefix="lamplight-engine-check-") as temporary, contextlib.ExitStack() as stack:
        directory = pathlib.Path(temporary) if args.check or args.capture else ROOT / "output" / "lamplight-native"
        stack.enter_context(single_library(directory))
        http = ThreadingHTTPServer(("127.0.0.1", 0), game_native.Handler)
        http.library = game_native.Library(directory)
        if args.check or args.capture:
            # Test-only provider double: the real gate/benchmark still run through HTTP.
            from unittest.mock import patch
            from test_lamplight_ai import provider_reply
            stack.enter_context(patch.object(game_server.requests, "post", side_effect=provider_reply))
        elif args.hyper:
            try:
                setup_hyper(http.library)
            except ValueError as error:
                print(f"AI setup: {error}. Retry from the game's AI menu.", flush=True)
        worker = threading.Thread(target=http.serve_forever, daemon=True)
        worker.start()
        environment = os.environ | {"LAMPLIGHT_URL": f"http://127.0.0.1:{http.server_port}/api/native",
                                    "LAMPLIGHT_TOKEN": game_server.TOKEN}
        (ROOT / ".cache").mkdir(exist_ok=True)
        command = [args.godot, "--path", str(ROOT / "godot"), "--rendering-method", "gl_compatibility",
                   "--log-file", str(ROOT / ".cache" / "godot-run.log")]
        if args.editor:
            command.append("--editor")
        if args.check:
            command += ["--headless", "--", "--check"]
        if args.capture:
            capture_dir = ROOT / "output" / "lamplight-engine-check"
            capture_dir.mkdir(parents=True, exist_ok=True)
            environment["LAMPLIGHT_CAPTURE_DIR"] = str(capture_dir)
            command += ["--position", "-32000,-32000", "--", "--capture"]
        startup = None
        if os.name == "nt" and (args.check or args.capture):
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = subprocess.SW_HIDE
        try:
            verifying = args.check or args.capture
            result = subprocess.run(command, env=environment, startupinfo=startup, timeout=90 if verifying else None,
                                    capture_output=verifying, text=True)
            if verifying:
                print(result.stdout, end="")
                print(result.stderr, end="")
                if "ERROR:" in result.stdout + result.stderr:
                    raise SystemExit(1)  # Godot can log script errors yet exit with code zero.
            raise SystemExit(result.returncode)
        finally:
            http.shutdown()
            http.server_close()
            worker.join(timeout=3)


if __name__ == "__main__":
    main()
