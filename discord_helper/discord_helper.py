import re
import discord
from discord.ext import commands
from discord import Intents
from typing import Callable

class DiscordHelper():

    def __init__(self, token: str, robot_name):
        self.current_user = None

        # definition of listeners
        self.on_ready_listener: Callable = None
        self.on_message_listener: Callable = None
        self.on_set_char_listener: Callable = None
        self.on_clear_user_messages: Callable = None

        # initalize
        self.robot_name = robot_name
        self.token = token
        self.is_flow_protection_enabled = False
        self.is_processing = False

        # Create Intents object
        intents = Intents.default()
        intents.message_content = True
        intents.typing = False
        intents.presences = False

        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.bot.add_listener(self.on_ready, 'on_ready')
        self.bot.add_listener(self.on_message, 'on_message')

        @self.bot.command()
        async def set_char(ctx: commands.Context, *, message: str):
            print(f'!set_char {message}')
            if self.on_set_char_listener is not None:
                self.on_set_char_listener(message)

        @self.bot.command()
        async def clear_user_messages(ctx: commands.Context):
            print(f'!clear_user_messages')
            if self.on_clear_user_messages is not None:
                self.on_clear_user_messages()
            await ctx.send('Done.')
            
    def run(self):
        self.bot.run(self.token)


    async def send_message(self, ctx: commands.Context, message: str):
        await ctx.send(message)

    def replace_mentions_with_names(self, ctx: commands.Context, message: str, replacement: str, names_to_replace: str) -> str:
        def replace_names(match):
            return replacement
        mention_matches = re.finditer(r'<@!?(\d+)>', message)
        for match in mention_matches:
            user_id = int(match.group(1))
            user = ctx.guild.get_member(user_id)
            if user:
                message = message.replace(match.group(0), user.display_name)
        message = re.sub(names_to_replace, replace_names, message)
        return message

    def set_flow_protection_enabled(self, enabled: bool):
        self.is_flow_protection_enabled = enabled

    def get_bot_username(self):
        return self.bot.user.name

    async def on_ready(self) -> None:
        if self.on_ready_listener is not None:
            await self.on_ready_listener()

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot: return
        if (self.robot_name not in message.content) and (not self.bot.user.mentioned_in(message)): return
        if self.on_message_listener is None:
            print('DiscordHelper: self.on_message_listener is None')
            return
        if self.is_flow_protection_enabled and self.is_processing:
            await message.reply('I am currently busy and cannot receive messages at the moment. Please send me a message later.')
            return
        
        self.is_processing = True

        ctx = await self.bot.get_context(message)
        if ctx.guild is not None or ctx.author.id == 414075282757255178: 
            await self.on_message_listener(message.content, ctx)

        self.is_processing = False

