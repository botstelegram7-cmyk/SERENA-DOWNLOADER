# Copyright (c) 2026 tusar404
# Licensed under the MIT License.

import os

from .. import LOGGER
from .config import config


def setup_directories() -> None:
    os.makedirs(config.download_dir, exist_ok=True)
    LOGGER.info("Working directory ready: %s", config.download_dir)
