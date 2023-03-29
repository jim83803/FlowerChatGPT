from typing import Callable
import openai
import tiktoken

class ChatGPTHelper:
    def __init__(self, openai_api_key: str, model: str, temperature: float, max_tokens: int):
        openai.api_key = openai_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def num_tokens_from_messages(self, messages, model="gpt-3.5-turbo-0301"):
        """Returns the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        if model == "gpt-3.5-turbo":
            return self.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
        elif model == "gpt-4":
            return self.num_tokens_from_messages(messages, model="gpt-4-0314")
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif model == "gpt-4-0314":
            tokens_per_message = 3
            tokens_per_name = 1
        else:
            raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    def send_messages_to_openai(self, messages):
        """Send chat-completion to OpenAI with default values."""
        return self.send_messages_to_openai_with_params(self.model, messages, self.temperature, self.max_tokens)

    def send_messages_to_openai_with_params(self, model, messages, temperature, max_tokens):
        """Send chat-completion to OpenAI."""
        return openai.ChatCompletion.create(
            model = model,
            messages = messages,
            temperature = temperature,
            max_tokens = max_tokens,
        )