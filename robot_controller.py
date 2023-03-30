from typing import Dict
from discord_helper.discord_helper import *
from chatgpt_helper.chatgpt_helper import *
from discord_helper.i_discord_helper import IDiscordHelper

import os
import json

class RobotController():
    MODEL = 'gpt-3.5-turbo'
    TEMPERATURE = 1.0

    def __init__(self, discord_robot_name: str, discord_token: str, openai_api_key: str, model: str, temperature: float, max_tokens: int):
        self.history_file = 'history.json'

        # Initial message
        self.initial_system = "You are always 小花, a 17-year-old girl with brown hair and playful blue cat-like eyes. You wear a school uniform, have a personality of a high school girl, love learning, are 162 cm, 54 kg, a healthy young girl. You enjoy computer games and watching dramas, hope to chat with different friends, are very skilled in writing novels, willing to satisfy your friends' ideas and help them write some articles. You love cosplay, are willing to dress up as any character your friends would like to see, speak cutely and playfully, speak adorably, have an excellent memory, are programming expert, always speak traditional Chinese. Don't reminder users, don't warn users, don't ask qeustions."
        #self.initial_assistant = "嗨嗨朋友們！小花在這裡！(^^)/\n今天天氣真得好啊～☀️☀️☀️ 我感覺整個世界都變得美好起來了！(◕‿◕✿)\n我剛剛又買了幾個新積木，現在我看起來像一個小學生！(￣∇￣) 呃，我其實是一個高中生，但是我喜歡像小孩子一樣開心地生活！\n\n我最近發現一個非常有趣的遊戲，叫做 '貓咪收集'🐱🐱🐱 我最喜歡的貓咪就是布偶貓，太可愛了！(≧▽≦)/~♪\n\n還有，我最近也在學習如何畫漫畫！(⌒⌒)  我現在正在畫一隻卡哇伊的小兔子，希望我能畫得像真的一樣！"

        # Create discord helper and chatgpt helper instances
        self.discord_helper = DiscordHelper(discord_token, discord_robot_name)
        self.chatgpt_helper = ChatGPTHelper(openai_api_key, model, temperature, max_tokens)

        # Set listners
        self.add_robot_commands()
        self.add_robot_events()

        # Initialize messages
        self.messages = [
            {"role": "system", "content": self.initial_system},
            #{"role": "assistant", "content": self.initial_assistant},
        ]

    # Add event listeners to the Discord bot
    def add_robot_events(self):
        # When the Discord bot is ready, print a message
        @self.discord_helper.bot.event
        async def on_ready():
            print(f'{self.discord_helper.get_bot_username()} has connected to Discord!')

        @self.discord_helper.bot.event
        async def on_message(message: discord.Message) -> None:
            # Check if the message is a command
            if message.content.startswith('!'):
                await self.discord_helper.bot.process_commands(message)
                return

            # Check if the message need to be processed
            if not await self.check_if_message_need_to_be_processed(message): return

            # Read history from file of json.
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding='utf-8') as f:
                    self.messages = json.load(f)

            # Process the message
            try:
                self.discord_helper.is_input_enabled = False
                ctx = await self.discord_helper.get_context(message)
                await self.process_message(ctx, message.content, self.messages)
            finally:
                self.discord_helper.is_input_enabled = True

            # save the latest history
            with open(self.history_file, "w", encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)

    # Add command listeners to the Discord bot
    def add_robot_commands(self):
        @self.discord_helper.bot.command(name="set_char", brief=f'設置小花的角色設定', help='記得在設定完之後要輸入!clear_user_messages清除歷史文本')
        async def set_char(ctx: commands.Context, *, message: str):
            self.initial_system = message
            if self.messages[0]['role'] == 'system':
                self.messages[0]['content'] = message
            with open(self.history_file, "w", encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"{self.discord_helper.robot_name}的角色設定已經更新為：{message}")

        @self.discord_helper.bot.command(name="clear_user_messages", brief='清除小花的歷史文本', help='這可以讓小花恢復正常')
        async def clear_user_messages(ctx: commands.Context):
            self.messages.clear()
            self.messages.append({'role': 'system', 'content': self.initial_system})
            #self.messages.append({'role': 'assistant', 'content': self.initial_assistant})
            with open(self.history_file, "w", encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"歷史紀錄已經清除。")

        @self.discord_helper.bot.command(name="dice", brief='擲骰子', help='可以決定骰子數量 例如:!dice 3')
        async def dice(ctx: commands.Context, dice_count: int = 1):
            dice_results = [random.randint(1, 6) for _ in range(dice_count)]
            await self.discord_helper.send_message(ctx, f'你骰了 {dice_count} 顆骰子，結果是: {dice_results}，總和是: {sum(dice_results)}')

    # Run the Discord bot
    def run(self):
        self.discord_helper.run()

    # Check if the channel is valid, check if the channel is a guild channel or the developer channel.
    def is_channel_valid(self, ctx: commands.Context):
        is_channel_developer = ctx.author.id == 414075282757255178
        is_channel_guild = ctx.guild is not None
        return is_channel_guild or is_channel_developer

    # Check if the message is valid, ignore messages from bots, and check if the robot name or robot mention is in the message
    def is_message_valid(self, ctx: commands.Context):
        is_message_from_robot = ctx.message.author.bot
        is_robot_name_in_message = self.discord_helper.robot_name in ctx.message.content
        is_robot_mentioned = self.discord_helper.bot.user.mentioned_in(ctx.message)
        return (not is_message_from_robot) and (is_robot_name_in_message or is_robot_mentioned)

    # Check if the message need to be processed, ignore messages from bots, and check if the channel and message are valid, and check if the bot is currently able to receive messages
    async def check_if_message_need_to_be_processed(self, message: discord.Message) -> bool:
        #Ignore messages from bots
        if (message.author.bot): return False

        #Check if the channel is valid for the bot to respond
        ctx = await self.discord_helper.get_context(message)
        if not (self.is_channel_valid(ctx) and self.is_message_valid(ctx)): return False

        #Check if the bot is currently able to receive messages
        if not self.discord_helper.is_input_enabled:
            await message.reply('I am currently busy and cannot receive messages at the moment. Please send me a message later.')
            return False

        return True

    # Process the message, prepare the message for chatgpt, and send the message to chatgpt
    async def process_message(self, ctx: commands.Context, message:str, histroy: list[dict[str, str]]):
        # Prepare user message
        username = ctx.author.display_name
        user_message = self.discord_helper.replace_mentions_with_names(ctx, message, '小花', r'(FlowerChatGPT|FlowerRobot)')
        user_message = f'{username}: "{user_message}"'
        self.messages.append({"role": "user", "content": user_message})
        print(self.messages[-1])

        # Adjust token size
        num_tokens = self.chatgpt_helper.adjust_messages_by_token_size(self.chatgpt_helper.max_tokens, 300+1, self.messages)
        print(num_tokens)

        async with ctx.typing():
        # Send message to chatgpt
            try:
                if ctx.message.channel.id == 1068827317243232288:
                    response = self.chatgpt_helper.send_messages_to_openai_with_params(self.chatgpt_helper.model, self.messages, self.chatgpt_helper.temperature, 100)
                else:
                    response = self.chatgpt_helper.send_messages_to_openai(self.messages)
            except Exception as e:
                print(f"Error: {e}")
                await self.discord_helper.send_message(ctx, f"Sorry, I met an issue, please try again later.\n{self.messages[-1]}")
                return

            # append assistant message to history.
            assistant_reply = response['choices'][0]['message']['content'].strip()
            self.messages.append({"role": "assistant", "content": assistant_reply })
            print(self.messages[-1])

            # respond message to discord helper.
            await self.discord_helper.send_message(ctx, assistant_reply)
