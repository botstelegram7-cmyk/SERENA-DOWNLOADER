# Licensed under the MIT License.
"""Root compatibility module for SERENA.

Allows existing workflows like `python -m bot` and `import bot` to function
seamlessly after migrating package internals to `serena/`.
"""

import asyncio

from serena import *
from serena.__main__ import main

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        if not loop.is_closed():
            loop.close()
