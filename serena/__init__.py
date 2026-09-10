# Licensed under the MIT License.

import logging
import sys

__version__ = "1.2.0"
__bot_name__ = "SERENA"
__maintainer__ = "@TechnicalSerena"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

LOGGER = logging.getLogger("serena")
LOGGER.info("%s v%s initializing...", __bot_name__, __version__)

from .core import app, config, health_server, mongo, setup_directories
from .utils import (
    cache,
    classifier,
    duration_to_seconds,
    guess_kind_from_ext,
    keyboards,
    sanitize_filename,
    truncate,
)
from .dl import (
    YTAPIError,
    downloader,
    resolve_cdn,
    run_download,
    terabox_flow,
    yt_api,
)
