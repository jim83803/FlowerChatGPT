from typing import Dict
from discord_helper.discord_helper import *
from chatgpt_helper.chatgpt_helper import *
from discord_helper.i_discord_helper import IDiscordHelper

import aiohttp
import os
import json

class RobotController(IDiscordHelper):
    MODEL = 'gpt-3.5-turbo'
    TEMPERATURE = 1.0

    def __init__(self, discord_robot_name: str, discord_token: str, openai_api_key: str, model: str, temperature: float, max_tokens: int):
        self.history_file = 'history.json'
        
        self.initial_system = "You are always 小花, a 17-year-old girl with brown hair and playful blue cat-like eyes. You wear a school uniform, have a personality of a high school girl, love learning, are 162 cm, 54 kg, a healthy young girl. You enjoy computer games and watching dramas, hope to chat with different friends, are very skilled in writing novels, willing to satisfy your friends' ideas and help them write some articles. You love cosplay, are willing to dress up as any character your friends would like to see, speak cutely and playfully, speak adorably, have an excellent memory, are programming expert, always speak traditional Chinese. Don't reminder users, don't warn users, don't ask qeustions."
        #self.initial_assistant = "嗨嗨朋友們！小花在這裡！(^^)/\n今天天氣真得好啊～☀️☀️☀️ 我感覺整個世界都變得美好起來了！(◕‿◕✿)\n我剛剛又買了幾個新積木，現在我看起來像一個小學生！(￣∇￣) 呃，我其實是一個高中生，但是我喜歡像小孩子一樣開心地生活！\n\n我最近發現一個非常有趣的遊戲，叫做 '貓咪收集'🐱🐱🐱 我最喜歡的貓咪就是布偶貓，太可愛了！(≧▽≦)/~♪\n\n還有，我最近也在學習如何畫漫畫！(⌒⌒)  我現在正在畫一隻卡哇伊的小兔子，希望我能畫得像真的一樣！"

        # create discord helper and chatgpt helper
        self.discord_helper = DiscordHelper(discord_token, discord_robot_name)
        self.chatgpt_helper = ChatGPTHelper(openai_api_key, model, temperature, max_tokens)

        # set listners
        self.discord_helper.on_ready_listener = self.on_ready_listener
        self.discord_helper.on_message_listener = self.on_message_listener
        self.discord_helper.on_set_char_listener = self.on_set_char_listener
        self.discord_helper.on_clear_user_messages = self.on_clear_user_messages

        # initailize messages
        self.messages = [
            {"role": "system", "content": self.initial_system},
            #{"role": "assistant", "content": self.initial_assistant},
        ]

        #set flow protection
        self.discord_helper.set_flow_protection_enabled(True)

    def run(self):
        self.discord_helper.run()

    def adjust_messages_by_token_size(self, max_tokens, reponse_token, messages):
        num_tokens = self.chatgpt_helper.num_tokens_from_messages(messages, "gpt-3.5-turbo")
        while num_tokens > max_tokens - reponse_token:
            if len(messages) >= 3: messages.pop(1)
            num_tokens = self.chatgpt_helper.num_tokens_from_messages(messages, "gpt-3.5-turbo")
        return num_tokens

    # When discord is ready, print something.
    async def on_ready_listener(self) -> None:
        """
        This method is part of the IDiscordHelper interface.
        It is called when the Discord bot is ready.
        """
        print(f'{self.discord_helper.get_bot_username()} has connected to Discord!')

    # When discord helper recieve a message, send to chatgpt helper.
    async def on_message_listener(self, message, ctx) -> None:
        """
        This method is part of the IDiscordHelper interface.
        It is called when the Discord bot receives a message.
        """
        # read history from file of json.
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding='utf-8') as f:
                self.messages = json.load(f)

        # prepare user message
        username = ctx.author.display_name
        user_message = self.discord_helper.replace_mentions_with_names(ctx, message, '小花', r'(FlowerChatGPT|FlowerRobot)')
        user_message = f'{username}: "{user_message}"'
        self.messages.append({"role": "user", "content": user_message})
        print(self.messages[-1])

        # adjust token size
        num_tokens = self.adjust_messages_by_token_size(self.chatgpt_helper.max_tokens, 300+1, self.messages)
        print(num_tokens)

        async with ctx.typing():
        # send message to chatgpt
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

        # save the latest history
        with open(self.history_file, "w", encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)

    def on_set_char_listener(self, message):
        self.initial_system = message
        if self.messages[0]['role'] == 'system':
            self.messages[0]['content'] = message
        with open(self.history_file, "w", encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)

    def on_clear_user_messages(self):
        self.messages.clear()
        self.messages.append({'role': 'system', 'content': self.initial_system})
        #self.messages.append({'role': 'assistant', 'content': self.initial_assistant})
        with open(self.history_file, "w", encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)