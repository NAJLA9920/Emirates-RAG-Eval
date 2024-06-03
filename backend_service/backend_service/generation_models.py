from typing import List, Optional, Dict
from abc import ABC, abstractmethod
import openai
from openai import OpenAI
import logging
import replicate
from openai import AsyncOpenAI
from fastapi.encoders import jsonable_encoder
import replicate.client
from backend_service.schema import MessagesRequest
from backend_service.custom_exceptions import RateLimitError, RetryAttemptsFailed, MaximumContextLengthReached



logger = logging.getLogger('backend_service_logger')



class LLMGen(ABC):
    """Interface for Generative LLM like ChatGPT or Claude"""

    def __init__(self, api_key: str, org: Optional[str]) -> None:
        pass

    @abstractmethod
    async def generate(self, history: List[dict]):
        """
        Abstract method to generate text based on the provided history of messages.

        Args:
            history (List[dict]): A list of message dictionaries representing the conversation history.

        Raises:
            NotImplementedError: This method must be overridden by subclasses.
        """
        raise NotImplementedError

    def _format_output(self, text: str):
        """
        Formats the generated text into a dictionary.

        Args:
            text (str): The generated text.

        Returns:
            dict: A dictionary containing the formatted text.
        """
        return { "text": text }

    async def generate_with_retry(self, data: MessagesRequest, max_attempts: int = 3):
        """
        Retries the text generation with a maximum number of attempts on failure.

        Args:
            data (MessagesRequest): The request data containing the messages.
            max_attempts (int): The maximum number of retry attempts. Default is 3.

        Returns:
            dict: The generated content.

        Raises:
            RetryAttemptsFailed: If all retry attempts fail.
        """
        decoded_messages = jsonable_encoder(data)
        prompts = decoded_messages['messages']
        logger.info("Requested with prompt: {}".format(prompts))
        # Retry by continuing the loop
        for idx in range(max_attempts):
            logger.info("Retry attempt: %d", idx + 1)
            try:
                generated_content = await self.generate(prompts)
                return generated_content
            except openai.APIConnectionError:
                logger.exception("API Connection Reset issue.")
            except RateLimitError:
                logger.exception("RateLimitError on Claude.")
            except openai.APITimeoutError as e:
                logger.exception(e)
                raise MaximumContextLengthReached(e)
        # All retry attempts failed, return empty result
        raise RetryAttemptsFailed("All attempts failed")


class OpenAIReg(LLMGen):
    """
    OpenAIReg is a subclass of LLMGen that uses the OpenAI API to generate text.

    Attributes:
        api_key (str): The API key for the OpenAI service.
        model (str): The name of the OpenAI model to use for generation.
        base_url (Optional[str]): The base URL for the OpenAI API.

    Methods:
        __init__(self, api_key: str, model: str, base_url: Optional[str] = None) -> None: Initializes the OpenAIReg class with the provided API key, model name, and optional base URL.

        async generate(self, messages: List[dict]) -> Dict[str, str]: Generates text based on the provided history of messages using the OpenAI API.

    """

    def __init__(self, api_key, model, base_url=None) -> None:
        """
        Initializes the OpenAIReg class with the provided API key, model name, and optional base URL.

        Args:
            api_key (str): The API key for the OpenAI service.
            model (str): The name of the OpenAI model to use for generation.
            base_url (Optional[str]): The base URL for the OpenAI API. Default is None.
        """
        self.model = model
        if base_url:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, messages: List[dict]):
        """
        Generates text based on the provided history of messages using the OpenAI API.

        Args:
            messages (List[dict]): A list of message dictionaries representing the conversation history.

        Returns:
            dict: A dictionary containing the generated text.
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            stop=[],
        )
        text = response.choices[0].message.content
        return self._format_output(text)
    
    
    

class OpenAIStream():
    """
    OpenAIStream is a subclass of LLMGen that uses the OpenAI API to generate text in a streaming manner.

    Attributes:
        api_key (str): The API key for the OpenAI service.
        model (str): The name of the OpenAI model to use for generation.

    Methods:
        __init__(self, api_key: str, model: str) -> None: Initializes the OpenAIStream class with the provided API key and model name.

        generate(self, user_query: List[Dict[str,str]]) -> Dict[str, str]: Generates text based on the provided user query using the OpenAI API in a streaming manner.

    """

    def __init__(self, api_key, model) -> None:
        """
        Initializes the OpenAIStream class with the provided API key and model name.

        Args:
            api_key (str): The API key for the OpenAI service.
            model (str): The name of the OpenAI model to use for generation.
        """
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate(self, user_query: List[Dict[str,str]]):
        """
        Generates text based on the provided user query using the OpenAI API in a streaming manner.

        Args:
            user_query (List[Dict[str,str]]): A list of dictionaries representing the user query.

        Returns:
            stream: A stream of generated text.
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=user_query,
            temperature=0.0,
            stream=True,
            stop=[],
        )
        return stream
    
    
    
class Replicate():
    """
    Replicate is a subclass of LLMGen that uses the Replicate API to generate text.

    Attributes:
        api_token (str): The API token for the Replicate service.
        model (str): The name of the Replicate model to use for generation.

    Methods:
        __init__(self, api_token: str, model: str) -> None: Initializes the Replicate class with the provided API token and model name.

        async generate(self, user_query: str) -> Dict[str, str]: Generates text based on the provided user query using the Replicate API.

    """
    def __init__(self,model:str, api_token: str) -> None:
        """
        Initializes the Replicate class with the provided API token and model name.

        Args:
            model (str): The name of the Replicate model to use for generation.
            api_token (str): The API token for the Replicate service.
        """
        self.model = model
        self.client = replicate.Client(api_token=api_token)
        
    def generate(self, user_query: str):
        """
        Generates text based on the provided user query using the Replicate API.

        Args:
            user_query (str): The user query as a string.

        Returns:
            stream: A stream of generated text.
        """
        input = {
            "top_p": 1,
            "prompt": user_query,
            "temperature": 0.0,
            "system_prompt": "You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\n\nIf a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.",
            "max_new_tokens": 10
        }

        return self.client.stream(
            self.model,
            input=input)



class ReplicateReg():
    """
    ReplicateReg is a subclass of LLMGen that uses the Replicate API to generate text with a custom system prompt.

    Attributes:
        api_token (str): The API token for the Replicate service.
        model (str): The name of the Replicate model to use for generation.

    Methods:
        __init__(self, api_token: str, model: str) -> None: Initializes the ReplicateReg class with the provided API token and model name.

        async generate(self, user_query: str) -> Dict[str, str]: Generates text based on the provided user query using the Replicate API with a custom system prompt.

    """
    def __init__(self,model:str, api_token: str) -> None:
        """
        Initializes the ReplicateReg class with the provided API token and model name.

        Args:
            model (str): The name of the Replicate model to use for generation.
            api_token (str): The API token for the Replicate service.
        """
        self.model = model
        self.client = replicate.Client(api_token=api_token)
    
    def _format_output(self, text: str):
        """
        Formats the generated text into a dictionary.

        Args:
            text (str): The generated text.

        Returns:
            dict: A dictionary containing the formatted text.
        """
        return { "text": text }
    
    async def generate(self, user_query: str):
        """
        Generates text based on the provided user query using the Replicate API with a custom system prompt.

        Args:
            user_query (str): The user query as a string.

        Returns:
            dict: A dictionary containing the generated text.
        """
        input = {
            "top_p": 1,
            "prompt": user_query,
            "temperature": 0.0,
            "system_prompt": "You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\n\nIf a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.",
            "max_new_tokens": 10
        }

        response = await self.client.async_run(self.model, input=input)
        return self._format_output(response)