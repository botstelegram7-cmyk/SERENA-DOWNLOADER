# Licensed under the MIT License.

from .. import LOGGER
from ..utils.helper import HandlerRegistry

start_registry = HandlerRegistry("serena.handlers.start")
search_registry = HandlerRegistry("serena.handlers.search")
callback_registry = HandlerRegistry("serena.handlers.callback")
inline_registry = HandlerRegistry("serena.handlers.inline")
admin_registry = HandlerRegistry("serena.handlers.admin")
clones_registry = HandlerRegistry("serena.handlers.clones")
lang_registry = HandlerRegistry("serena.handlers.lang")

from . import admin, callback, clones, inline, lang, search, start


def attach_shared_handlers(client) -> None:
    for module in (start, search, callback, inline, lang):
        module.registry.attach(client)


LOGGER.info(
    "Handlers loaded -> %s",
    ", ".join(m.registry.name.rsplit(".", 1)[-1] for m in (start, search, callback, inline, admin, clones, lang)),
)
