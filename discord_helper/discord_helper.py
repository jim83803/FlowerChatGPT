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
        self.bot.add_listener(self.on_ready, 'on_ready')
        self.bot.add_listener(self.on_message, 'on_message')

        @self.bot.command(name='set_char', brief='設置小花的角色設定', help='設置小花的角色設定')
        async def set_char(ctx: commands.Context, *, message: str):
            print(f'!set_char {message}')
            if self.on_set_char_listener is not None:
                self.on_set_char_listener(message)

        @self.bot.command(name='clear_user_messages', brief="清除歷史文本", help="這可以讓小花恢復正常")
        async def clear_user_messages(ctx: commands.Context):
            print(f'!clear_user_messages')
            if self.on_clear_user_messages is not None:
                self.on_clear_user_messages()
            await ctx.send('Done.')

        @self.bot.command(name='dice', brief="骰骰子", help="可以決定骰子數量 例如:!dice 3")
        async def dice(ctx: commands.Context, dice_count: int = 1):
            dice_results = [random.randint(1, 6) for _ in range(dice_count)]
            await ctx.send(f'你骰了 {dice_count} 顆骰子，結果是: {dice_results}，總和是: {sum(dice_results)}')

    def run(self):
        self.bot.run(self.token)

    async def send_message(self, ctx: commands.Context, message: str):
        await ctx.send(message)

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

    def get_bot_username(self):
        return self.bot.user.name

    async def on_ready(self) -> None:
        if self.on_ready_listener is not None:
            await self.on_ready_listener()

    async def on_message(self, message: discord.Message) -> None:
        # Ignore messages from bots
        if (message.author.bot):
            return

        # Check if the bot is currently able to receive messages
        if not self.is_input_enabled:
            await message.reply('I am currently busy and cannot receive messages at the moment. Please send me a message later.')
            return

        # If no listener is set for on_message, print a warning
        if self.on_message_listener is None:
            print('DiscordHelper: self.on_message_listener is None')
            return

        # Process the message with the listener
        ctx = await self.bot.get_context(message)
        await self.on_message_listener(message.content, ctx)