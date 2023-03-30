from typing import Callable, Dict, List
import openai
import tiktoken

class ChatGPTHelper:
    def __init__(self, openai_api_key: str, model: str, temperature: float, max_tokens: int):
        openai.api_key = openai_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    # Calculate the number of tokens used by a list of messages
    def calculate_token_counts(self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo-0301") -> int:
        """Returns the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        if model == "gpt-3.5-turbo":
            return self.calculate_token_counts(messages, model="gpt-3.5-turbo-0301")
        elif model == "gpt-4":
            return self.calculate_token_counts(messages, model="gpt-4-0314")
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

    # Adjust the number of tokens according to the token size
    def adjust_messages_by_token_size(self, max_tokens: int, reponse_token: int, messages: List[Dict[str, str]]) -> int:
        num_tokens = self.calculate_token_counts(messages, "gpt-3.5-turbo")
        while num_tokens > max_tokens - reponse_token:
            if len(messages) >= 3: messages.pop(1)
            num_tokens = self.calculate_token_counts(messages, "gpt-3.5-turbo")
        return num_tokens

    # Send messages to OpenAI and return the response, using the default parameters
    def send_messages_to_openai(self, messages: List[Dict[str, str]]) -> Dict[str, str]:
        return self.send_messages_to_openai_with_params(self.model, messages, self.temperature, self.max_tokens)

    # Send messages to OpenAI and return the response
    def send_messages_to_openai_with_params(self, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> Dict[str, str]:
        """Send chat-completion to OpenAI."""
        return openai.ChatCompletion.create(
            model = model,
            messages = messages,
            temperature = temperature,
            max_tokens = max_tokens,
        )