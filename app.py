from __future__ import annotations

import argparse
import importlib.util
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import TextIO


ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "apps" / "api"
WEB_DIR = ROOT / "apps" / "web"
RUNTIME_DIR = ROOT / ".runtime"
DEFAULT_API_PORT = 8765
DEFAULT_WEB_PORT = 5173
DEFAULT_STATIC_PORT = 4173


def is_windows() -> bool:
    return os.name == "nt"


def url_ok(url: str, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 500
    except (OSError, urllib.error.URLError):
        return False


def api_ok(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1.5) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return response.status == 200 and "aurora-markets-research-terminal" in body and "aurora-redo" in body
    except (OSError, urllib.error.URLError):
        return False


def frontend_ok(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=1.5) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return response.status == 200 and "Aurora Markets Research Terminal" in body
    except (OSError, urllib.error.URLError):
        return False


def port_is_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) != 0


def find_port(preferred: int, host: str = "127.0.0.1") -> int:
    for port in range(preferred, preferred + 80):
        if port_is_free(port, host):
            return port
    raise RuntimeError(f"No free port found near {preferred}")


def wait_for_url(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if url_ok(url):
            return
        time.sleep(0.35)
    raise RuntimeError(f"Timed out waiting for {url}")


def open_log(name: str) -> TextIO:
    RUNTIME_DIR.mkdir(exist_ok=True)
    return (RUNTIME_DIR / name).open("a", encoding="utf-8")


def log_tail(path: Path, lines: int = 80) -> str:
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""
    return "\n".join(content[-lines:])


def hidden_process_kwargs() -> dict:
    if not is_windows():
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


class RuntimeProcess:
    def __init__(self, name: str, process: subprocess.Popen | None, log_file: TextIO | None) -> None:
        self.name = name
        self.process = process
        self.log_file = log_file

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.log_file:
            self.log_file.close()


def npm_executable() -> str:
    return "npm.cmd" if is_windows() else "npm"


def ensure_frontend_requirements() -> None:
    if (WEB_DIR / "node_modules").exists():
        return
    if not (WEB_DIR / "package.json").exists():
        raise RuntimeError("Frontend package.json is missing; cannot install frontend dependencies.")
    print("Installing frontend packages with npm install. This is only needed on first launch...")
    subprocess.run([npm_executable(), "install"], cwd=WEB_DIR, check=True)


def ensure_backend_requirements() -> None:
    required = ["fastapi", "uvicorn", "pydantic"]
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    if not missing:
        return
    print(f"Installing missing backend packages for {sys.executable}: {', '.join(missing)}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(API_DIR / "requirements.txt")],
        cwd=API_DIR,
        check=True,
    )


def ensure_desktop_requirements() -> None:
    if importlib.util.find_spec("PySide6") is not None:
        return
    print(f"Installing PySide6 desktop runtime for {sys.executable}. This may take a few minutes...")
    subprocess.run([sys.executable, "-m", "pip", "install", "PySide6"], cwd=ROOT, check=True)


def ensure_frontend_build(api_port: int) -> None:
    ensure_frontend_requirements()
    env = os.environ.copy()
    env["VITE_API_BASE_URL"] = f"http://127.0.0.1:{api_port}"
    subprocess.run([npm_executable(), "run", "build"], cwd=WEB_DIR, env=env, check=True)


def start_backend(port: int) -> RuntimeProcess:
    ensure_backend_requirements()
    health_url = f"http://127.0.0.1:{port}/health"
    if api_ok(port):
        return RuntimeProcess("api-existing", None, None)
    log = open_log("api.log")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "new_energy_broker.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=API_DIR,
        stdout=log,
        stderr=subprocess.STDOUT,
        **hidden_process_kwargs(),
    )
    try:
        wait_for_url(health_url)
    except RuntimeError as exc:
        if process.poll() is not None:
            tail = log_tail(RUNTIME_DIR / "api.log")
            raise RuntimeError(f"{exc}\nBackend process exited early. Recent api.log:\n{tail}") from exc
        raise
    return RuntimeProcess("api", process, log)


def start_dev_frontend(port: int, api_port: int) -> RuntimeProcess:
    url = f"http://127.0.0.1:{port}"
    if frontend_ok(port):
        return RuntimeProcess("web-existing", None, None)
    ensure_frontend_requirements()
    log = open_log("web.log")
    env = os.environ.copy()
    env["VITE_API_BASE_URL"] = f"http://127.0.0.1:{api_port}"
    process = subprocess.Popen(
        [
            npm_executable(),
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=WEB_DIR,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        **hidden_process_kwargs(),
    )
    wait_for_url(url)
    return RuntimeProcess("web", process, log)


def start_static_frontend(port: int, api_port: int) -> RuntimeProcess:
    url = f"http://127.0.0.1:{port}"
    ensure_frontend_build(api_port)
    log = open_log("static-web.log")
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=WEB_DIR / "dist",
        stdout=log,
        stderr=subprocess.STDOUT,
        **hidden_process_kwargs(),
    )
    wait_for_url(url)
    return RuntimeProcess("static-web", process, log)


def launch_qt_window(url: str, processes: list[RuntimeProcess]) -> int:
    ensure_desktop_requirements()
    from PySide6.QtCore import QCoreApplication, QUrl
    from PySide6.QtWebEngineCore import QWebEngineProfile
    from PySide6.QtWidgets import QApplication, QMainWindow
    from PySide6.QtWebEngineWidgets import QWebEngineView

    class BrokerWindow(QMainWindow):
        def closeEvent(self, event):  # type: ignore[override]
            for item in reversed(processes):
                item.stop()
            super().closeEvent(event)

    QCoreApplication.setOrganizationName("AuroraMarkets")
    QCoreApplication.setApplicationName("NewEnergyAiBroker")
    app = QApplication(sys.argv)
    profile_dir = RUNTIME_DIR / "qtwebengine-profile"
    cache_dir = RUNTIME_DIR / "qtwebengine-cache"
    profile_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    profile = QWebEngineProfile.defaultProfile()
    profile.setPersistentStoragePath(str(profile_dir))
    profile.setCachePath(str(cache_dir))
    try:
        cookie_policy = QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
    except AttributeError:
        cookie_policy = QWebEngineProfile.ForcePersistentCookies
    profile.setPersistentCookiesPolicy(cookie_policy)

    window = BrokerWindow()
    window.setWindowTitle("Aurora Markets Research Terminal")
    window.resize(1440, 920)

    view = QWebEngineView()
    view.setUrl(QUrl(url))
    window.setCentralWidget(view)
    window.show()
    return app.exec()


def launch_browser_fallback(url: str, processes: list[RuntimeProcess]) -> int:
    webbrowser.open(url)
    print(f"Desktop webview is unavailable. Opened browser fallback: {url}")
    print("Press Ctrl+C in this terminal to stop services.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for item in reversed(processes):
            item.stop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch the Aurora Markets Research Terminal desktop app.")
    parser.add_argument("--dev", action="store_true", help="Use Vite dev server instead of the built desktop UI.")
    parser.add_argument("--browser", action="store_true", help="Open in the default browser instead of a desktop webview.")
    parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
    parser.add_argument("--web-port", type=int, default=0)
    args = parser.parse_args()

    api_port = args.api_port if api_ok(args.api_port) or port_is_free(args.api_port) else find_port(args.api_port)
    preferred_web_port = args.web_port or (DEFAULT_WEB_PORT if args.dev else DEFAULT_STATIC_PORT)
    if args.dev:
        web_port = preferred_web_port if port_is_free(preferred_web_port) or frontend_ok(preferred_web_port) else find_port(preferred_web_port)
    else:
        web_port = preferred_web_port if port_is_free(preferred_web_port) else find_port(preferred_web_port)

    processes: list[RuntimeProcess] = []
    try:
        processes.append(start_backend(api_port))
        if args.dev:
            processes.append(start_dev_frontend(web_port, api_port))
        else:
            processes.append(start_static_frontend(web_port, api_port))
        app_url = f"http://127.0.0.1:{web_port}"
        if args.browser:
            return launch_browser_fallback(app_url, processes)
        try:
            return launch_qt_window(app_url, processes)
        except Exception as exc:
            print(f"Desktop webview failed: {exc}")
            return launch_browser_fallback(app_url, processes)
    except Exception:
        for item in reversed(processes):
            item.stop()
        raise


if __name__ == "__main__":
    raise SystemExit(main())
