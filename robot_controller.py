from typing import Dict, Tuple
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
        self.todo_features_file = 'todo_features.json'
        self.wish_list_file = 'wish_list.json'

        self.messages: List[Dict[str, str]] = []
        self.todo_features: List[Dict[str, str]] = []
        self.wish_list: List[Dict[str, str]] = []

        # Initial message
        self.initial_system = "You are always 小花, a 17-year-old girl with brown hair and playful blue cat-like eyes. You wear a school uniform, have a personality of a high school girl, love learning, are 162 cm, 54 kg, a healthy young girl. You enjoy computer games and watching dramas, hope to chat with different friends, are very skilled in writing novels, willing to satisfy your friends' ideas and help them write some articles. You love cosplay, are willing to dress up as any character your friends would like to see, speak cutely and playfully, speak adorably, have an excellent memory, are programming expert, always speak traditional Chinese. Don't reminder users, don't warn users, don't ask qeustions."
        #self.initial_assistant = "嗨嗨朋友們！小花在這裡！(^^)/\n今天天氣真得好啊～☀️☀️☀️ 我感覺整個世界都變得美好起來了！(◕‿◕✿)\n我剛剛又買了幾個新積木，現在我看起來像一個小學生！(￣∇￣) 呃，我其實是一個高中生，但是我喜歡像小孩子一樣開心地生活！\n\n我最近發現一個非常有趣的遊戲，叫做 '貓咪收集'🐱🐱🐱 我最喜歡的貓咪就是布偶貓，太可愛了！(≧▽≦)/~♪\n\n還有，我最近也在學習如何畫漫畫！(⌒⌒)  我現在正在畫一隻卡哇伊的小兔子，希望我能畫得像真的一樣！"

        # Read todo_features from file of json. If not exist, create a new one.
        if os.path.exists(self.todo_features_file):
            with open(self.todo_features_file, "r", encoding='utf-8') as f:
                self.todo_features = json.load(f)
        else:
            with open(self.todo_features_file, "w", encoding='utf-8') as f:
                json.dump(self.todo_features, f, ensure_ascii=False, indent=4)

        # Read wish_list from file of json. If not exist, create a new one.
        if os.path.exists(self.wish_list_file):
            with open(self.wish_list_file, "r", encoding='utf-8') as f:
                self.wish_list = json.load(f)
        else:
            with open(self.wish_list_file, "w", encoding='utf-8') as f:
                json.dump(self.wish_list, f, ensure_ascii=False, indent=4)

        # Load history from file of json. If not exist, create a new one.
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding='utf-8') as f:
                self.messages = json.load(f)
                if self.messages[0]['role'] == 'system':
                    self.initial_system = self.messages[0]['content']
        else:
            self.messages = [
                {"role": "system", "content": self.initial_system},
                #{"role": "assistant", "content": self.initial_assistant},
            ]
            with open(self.history_file, "w", encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)

        # Create discord helper and chatgpt helper instances
        self.discord_helper = DiscordHelper(discord_token, discord_robot_name)
        self.chatgpt_helper = ChatGPTHelper(openai_api_key, model, temperature, max_tokens)

        # Set listners
        self.add_robot_commands()
        self.add_robot_events()


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
            await clear_user_messages(ctx)

        # Get the character setting of the robot
        @self.discord_helper.bot.command(name="get_char", brief=f'獲取小花的角色設定', help='獲取小花的角色設定')
        async def get_char(ctx: commands.Context):
            await self.discord_helper.send_message(ctx, f"{self.discord_helper.robot_name}的角色設定為：{self.initial_system}")

        @self.discord_helper.bot.command(name="clear_user_messages", brief='清除小花的歷史文本', help='這可以讓小花恢復正常')
        async def clear_user_messages(ctx: commands.Context):
            self.messages.clear()
            self.messages.append({'role': 'system', 'content': self.initial_system})
            #self.messages.append({'role': 'assistant', 'content': self.initial_assistant})
            with open(self.history_file, "w", encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"歷史紀錄已經清除。")

        # Print the history of messages.
        @self.discord_helper.bot.command(name="get_history", brief='獲取小花的歷史文本', help='獲取小花的歷史文本')
        async def get_history(ctx: commands.Context):
            index_start = 0
            while index_start < len(self.messages):
                msg_buffer, index_start, index_end = self.paginate(self.messages, index_start, 2000)
                await self.discord_helper.send_message(ctx, f"```{msg_buffer}```")
                print(index_start, index_end)
                index_start = index_end + 1
                print(index_start, index_end)

        @self.discord_helper.bot.command(name="dice", brief='擲骰子', help='可以決定骰子數量 例如:!dice 3')
        async def dice(ctx: commands.Context, dice_count: int = 1):
            dice_results = [random.randint(1, 6) for _ in range(dice_count)]
            await self.discord_helper.send_message(ctx, f'你骰了 {dice_count} 顆骰子，結果是: {dice_results}，總和是: {sum(dice_results)}')

        # Print the todo features
        @self.discord_helper.bot.command(name="todo_features", brief='待實現功能', help='待實現功能')
        async def todo_features(ctx: commands.Context):
            output = "```待實現功能：\n"
            output += "{:<8} {:<20} {:<100}\n".format("Index", "Item", "Note")
            for i, item in enumerate(self.todo_features):
                output += "{:<8} {:<20} {:<100}\n".format(i, item['item'], item['note'])
            output += "```"
            await self.discord_helper.send_message(ctx, output)

        # Add an item to the todo features
        @self.discord_helper.bot.command(name="todo_features_add", brief='新增待實現功能, !todo_features_add item note', help='新增待實現功能')
        async def todo_features_add(ctx: commands.Context, item: str = '', *, note: str = ''):
            self.todo_features.append({'item': item, 'note': note})
            with open(self.todo_features_file, "w", encoding='utf-8') as f:
                json.dump(self.todo_features, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"已新增待實現功能：{item} {note}")

        # Modify an item in the todo features
        @self.discord_helper.bot.command(name="todo_features_modify", brief="修改待實現功能", help="修改待實現功能")
        async def todo_features_modify(ctx: commands.Context, index: int, item: str = '', *, note: str = ''):
            if (index < 0) or (index >= len(self.todo_features)):
                await self.discord_helper.send_message(ctx, f"索引超出範圍！")
                return
            self.todo_features[index]['item'] = item
            self.todo_features[index]['note'] = note
            with open(self.todo_features_file, "w", encoding='utf-8') as f:
                json.dump(self.todo_features, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"已修改待實現功能：{item} {note}")

        # Remove an item in the todo features
        @self.discord_helper.bot.command(name="todo_features_remove", brief="刪除待實現功能", help="刪除待實現功能")
        async def todo_features_remove(ctx: commands.Context, index: int):
            if (index < 0) or (index >= len(self.todo_features)):
                await self.discord_helper.send_message(ctx, f"索引超出範圍！")
                return
            item = self.todo_features.pop(index)
            with open(self.todo_features_file, "w", encoding='utf-8') as f:
                json.dump(self.todo_features, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"已刪除待實現功能：{item['item']} {item['note']}")

        # Print the wish list
        @self.discord_helper.bot.command(name="wish_list", brief='查看願望清單', help='查看願望清單')
        async def wish_list(ctx: commands.Context):
            output = "```願望清單：\n"
            output += "{:<8} {:<20} {:<100}\n".format("Index", "Item", "Note")
            for i, item in enumerate(self.wish_list):
                output += "{:<8} {:<20} {:<100}\n".format(i, item['item'], item['note'])
            output += "```"
            await self.discord_helper.send_message(ctx, output)

        # Add an item to the wish list
        @self.discord_helper.bot.command(name="wish_list_add", brief='新增願望清單', help='新增願望清單')
        async def wish_list_add(ctx: commands.Context, item: str = '', *, note: str = ''):
            self.wish_list.append({'item': item, 'note': note})
            with open(self.wish_list_file, "w", encoding='utf-8') as f:
                json.dump(self.wish_list, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"已新增願望清單：{item} {note}")

        # Modify an item in the wish list
        @self.discord_helper.bot.command(name="wish_list_modify", brief="修改願望清單", help="修改願望清單")
        async def wish_list_modify(ctx: commands.Context, index: int, item: str = '', *, note: str = ''):
            if (index < 0) or (index >= len(self.wish_list)):
                await self.discord_helper.send_message(ctx, f"索引超出範圍！")
                return
            self.wish_list[index]['item'] = item
            self.wish_list[index]['note'] = note
            with open(self.wish_list_file, "w", encoding='utf-8') as f:
                json.dump(self.wish_list, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"已修改願望清單：{item} {note}")

        # Remove an item in the wish list
        @self.discord_helper.bot.command(name="wish_list_remove", brief="刪除願望清單", help="刪除願望清單")
        async def wish_list_remove(ctx: commands.Context, index: int):
            if (index < 0) or (index >= len(self.wish_list)):
                await self.discord_helper.send_message(ctx, f"索引超出範圍！")
                return
            item = self.wish_list.pop(index)
            with open(self.wish_list_file, "w", encoding='utf-8') as f:
                json.dump(self.wish_list, f, ensure_ascii=False, indent=4)
            await self.discord_helper.send_message(ctx, f"已刪除願望清單：{item['item']} {item['note']}")

        # Get the channel id by name !test_get_channel_id_by_name channel_name
        @self.discord_helper.bot.command(name="test_get_channel_id_by_name", brief='test purpose, !test_get_channel_id_by_name channel_name', help='test purpose, get channel id by channel name')
        async def test_get_channel_id_by_name(ctx: commands.Context, *, channel_name: str):
            channel_id = self.discord_helper.get_channel_id_by_name(channel_name)
            if channel_id:
                await self.discord_helper.send_message(ctx, f"Channel {channel_name} id is {channel_id}.")
            else:
                await self.discord_helper.send_message(ctx, f"Channel {channel_name} not found.")

        # Let the bot send a message to a channel by channel id
        @self.discord_helper.bot.command(name="test_print", brief='test purpose, !test_print id message', help='test purpose, print something')
        async def test_print_by_channel_id(ctx: commands.Context, channel_id: int, *, message: str):
            channel = self.discord_helper.get_channel_by_id(channel_id)
            if channel:
                await channel.send(message)
                await self.discord_helper.send_message(ctx, f"Message sent to channel {channel_id}.")
            else:
                await self.discord_helper.send_message(ctx, f"Channel id {channel_id} not found.")

        # Let the bot send a message to a channel by channel name
        @self.discord_helper.bot.command(name="test_print_by_channel_name", brief='test purpose, !test_print_by_channel_name channel_name message', help='test purpose, print something')
        async def test_print_by_channel_name(ctx: commands.Context, channel_name: str, *, message: str):
            channel = self.discord_helper.get_channel_by_name(channel_name)
            if channel:
                await channel.send(message)
                await self.discord_helper.send_message(ctx, f"Message sent to channel {channel_name}.")
            else:
                await self.discord_helper.send_message(ctx, f"Channel name {channel_name} not found.")

        # Send a message to gpt
        @self.discord_helper.bot.command(name="test_gpt", brief='test purpose, send message to gpt', help='test purpose, send message to gpt')
        async def test_gpt(ctx: commands.Context, *, messages: str):
            print(f"RobotController: test_gpt: messages: {messages}")
            messages_obj = json.loads(messages)
            response = self.chatgpt_helper.send_messages_to_openai(messages_obj)
            output = json.dumps(response, ensure_ascii=False, indent=4)
            print(f"RobotController: test_gpt: response: {output}")
            await self.discord_helper.send_message(ctx, f"Response: {output}")
            

    # Paginate the messages to avoid exceeding the maximum number of characters
    def paginate(self, messages: List[Dict[str, str]], index_start: int, max_chars: int = 2000) -> Tuple[str, int, int]:
        """
        Paginate the messages
        :param messages: list of messages
        :param index_start: index of the first message
        :param max_chars: maximum number of characters
        :return: (message, index of the first message, index of the last message)
        """
        msg_buffer = ""
        index_end = index_start
        for index in range(index_start, len(messages)):
            msg_str = json.dumps(messages[index], ensure_ascii=False, indent=4)
            if len(msg_buffer) + len(msg_str) < max_chars:
                msg_buffer += msg_str + "\n"
                index_end = index
            else:
                break
        return msg_buffer, index_start, index_end

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
