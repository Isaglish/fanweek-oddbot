"""
Useful utilities I can use to help with coding.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import TYPE_CHECKING

from discord.ext import commands

from . import app_commands as app_commands
from . import embed as embed
from . import submission as submission

if TYPE_CHECKING:
    from bot import Bot


__all__ = (
    "Context",
)


Context = commands.Context["Bot"]
