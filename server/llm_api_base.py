from server.llm_mesage import LllMessage
from typing import Callable, Coroutine, Union

import asyncio
import aiohttp
import inspect
import logging

'''Base class for wrapping an LLM API.'''
class LlmApiBase:
    '''Initializes the API client.

    Args:
    - name (str): LLM API vendor name.
    - url (str): URL target for CURLing the API.
    - api_key (str): API key for the LLM API.
    - header (dict): static HTTP header for invoking the HTTP API.
    - prompt_to_data (function): transforms prompt string to the HTTP body.
    - response_extraction_callbck (function|coroutine): extract HTTP response.
    '''
    def __init__(
            self,
            name: str,
            url: str, 
            api_key: str, 
            headers: dict=None,
            prompt_to_data: Callable[[str], dict]=None,
            response_extraction_callbck: Union[
                Callable[[dict], str],
                Coroutine[None, dict, str]]=None,
            ai_agent: 'AiAgent'=None):
        self.name = name
        self.url = url
        self.api_key = api_key
        if not headers:
            headers = {}
        self.headers = headers
        if not prompt_to_data:
            prompt_to_data = lambda _: {}
        self.prompt_to_data = prompt_to_data
        if not response_extraction_callbck: response_extraction_callbck = str
        self.response_extraction_callbck = response_extraction_callbck
        self.ai_agent = ai_agent


    async def call_llm_api(self, data):
        '''Call LLM API
        
        Args:
        - data (dict): forms the API request body.

        Returns LLM response.
        '''
        print(f'[LlmApiBase] call_llm_api data: {data}')
        headers = self.headers

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=self.url, headers=headers, json=data) as response:
                response_data = await response.json()
                return response_data


    '''Prompts the LLM API.

    Optionally can provide history to send additional context.
    '''
    async def query(self, prompt) -> str:
        data = self.prompt_to_data(prompt)
        response_data = await self.call_llm_api(data)
        reply = ''
        try:
            if inspect.iscoroutinefunction(self.response_extraction_callbck):
                reply = await self.response_extraction_callbck(response_data)
            elif callable(self.response_extraction_callbck):
                reply = self.response_extraction_callbck(response_data)
            else:
                raise RuntimeError(
                    'Invalid type for response_extraction_callbck')
            print(f'[LlmApiBase] reply={reply}')
            return reply
        except Exception as ex:
            logging.error(str(ex))
            return str(response_data)
