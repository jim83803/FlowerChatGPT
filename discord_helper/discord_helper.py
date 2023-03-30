import random
import re
import discord
from discord.ext import commands
from discord import Intents
from typing import Callable

class DiscordHelper():

    def __init__(self, token: str, robot_name):
        self.current_user = None

        # Definition of listeners
        self.on_ready_listener: Callable = None
        self.on_message_listener: Callable = None
        self.on_set_char_listener: Callable = None
        self.on_clear_user_messages: Callable = None

        # Initalize
        self.robot_name = robot_name
        self.token = token
        self.is_input_enabled = True

        # Create Intents object
        intents = Intents.default()
        intents.message_content = True
        intents.typing = False
        intents.presences = False

        # Define bot commands
        self.bot = commands.Bot(command_prefix='!', intents=intents)

    # Start the Discord bot
    def run(self):
        self.bot.run(self.token)

    # Get the bot's username
    def get_bot_username(self):
        return self.bot.user.name

    # Get context from message
    async def get_context(self, message: discord.Message):
        return await self.bot.get_context(message)

    # Send message to the context that the message was received from
    async def send_message(self, ctx: commands.Context, message: str):
        await ctx.send(message)

    # Replace mentions with names, and replace names with given string
    def replace_mentions_with_names(self, ctx: commands.Context, message: str, replacement: str, names_to_replace: str) -> str:
        def replace_names(match):
            return replacement

        # Replace mentions with names
        mention_matches = re.finditer(r'<@!?(\d+)>', message)
        for match in mention_matches:
            user_id = int(match.group(1))
            user = ctx.guild.get_member(user_id)
            if user:
                message = message.replace(match.group(0), user.display_name)

        # Replace names with given string
        message = re.sub(names_to_replace, replace_names, message)
        return message