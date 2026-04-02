import multiprocessing
import os
import sys
import threading
import webbrowser

import uvicorn
from main import app

PORT = 8111
HOST = "127.0.0.1"


def _base_dir() -> str:
    """Return the directory that contains bundled resources.
    sys._MEIPASS is set by PyInstaller (both --onefile and --onedir).
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def open_browser() -> None:
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    # Required on Windows when using --onefile so spawned subprocesses
    # don't re-execute the whole bundle.
    multiprocessing.freeze_support()

    os.environ["BASE_DIR"] = _base_dir()

    # Open the browser shortly after the server starts
    threading.Timer(1.5, open_browser).start()

    print(f"Starting E*Trade G&L Viewer at http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
