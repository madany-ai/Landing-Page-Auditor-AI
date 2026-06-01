#!/usr/bin/env python3
"""
GUI entry point for Landing Page Auditor AI.

Run with:
    python gui_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on the Python path regardless of CWD
sys.path.insert(0, str(Path(__file__).parent))

from config.logging import setup_logging
setup_logging()

from gui.app import AuditorApp


if __name__ == "__main__":
    app = AuditorApp()
    app.mainloop()
