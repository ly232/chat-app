from typing import Callable

import aiohttp
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
    - response_extraction_callbck (function): extracts HTTP response.
    '''
    def __init__(
            self,
            name: str,
            url: str, 
            api_key: str, 
            headers: dict=None,
            prompt_to_data: Callable[[str], dict]=None,
            response_extraction_callbck: Callable[[dict], str]=None):
        self.name = name
        self.url = url
        self.api_key = api_key
        if not headers:
            headers = {}
        self.headers = headers
        if not prompt_to_data:
            prompt_to_data = lambda _: {}
        self.prompt_to_data = prompt_to_data
        if not response_extraction_callbck:
            response_extraction_callbck = str
        self.response_extraction_callbck = response_extraction_callbck

    '''Prompts the LLM API.

    Optionally can provide history to send additional context.
    '''
    async def query(self, prompt) -> str:
        headers = self.headers
        data = self.prompt_to_data(prompt)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=self.url, headers=headers, json=data) as response:
                response_data = await response.json()
                try:
                    return self.response_extraction_callbck(response_data)
                except Exception as ex:
                    logging.error(str(ex))
                    return str(response_data)

    