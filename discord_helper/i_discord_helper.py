import discord
from discord.ext import commands
from typing import Callable
from abc import ABC, abstractclassmethod

class IDiscordHelper(ABC):
    @abstractclassmethod
    async def on_ready_listener(self) -> None:
        pass

    @abstractclassmethod
    async def on_message_listener(self, message: discord.Message, ctx: commands.Context) -> None:
        pass