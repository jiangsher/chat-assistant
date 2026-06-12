from __future__ import annotations

import sys

from recognize.storage.config_store import ConfigStore
from recognize.ui.floating_window import run_floating_window
from recognize.utils.logging import configure_logging


def main() -> int:
    configure_logging()
    config_store = ConfigStore.default()
    return run_floating_window(config_store, sys.argv)
