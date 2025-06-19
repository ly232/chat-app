from anthropic import AnthropicRestClient
from gemini import GeminiRestClient
from openai import OpenAiRestClient
from protos.generated_pb2 import chat_service_pb2

import asyncio
import logging

class AiAgent:
  '''Proxy to talk to LLM APIs.
  '''

  def __init__(self, chat_server):
    self.chat_server = chat_server
    self.llm_apis = {
      '@google': GeminiRestClient(),
      '@gemini': GeminiRestClient(),
      '@anthropic': AnthropicRestClient(),
      '@claude': AnthropicRestClient(),
      '@openai': OpenAiRestClient(),
    }

  '''Internal method to first invoke llm api, then broadcast to channel.'''
  async def _single_llm_call(self, llm_api, prompt, channel):
    reply = await llm_api.query(prompt)
    await self.chat_server._broadcast(
        channel,
        chat_service_pb2.ChatMessage(
          sender_id=llm_api.name,
          content='\n\n' + reply + '\n\n'))

  async def query(self, prompt, connected_grpc_channels_copy):
    '''Sends prompt to relevant LLM APIs.

    Intends to support Anthropic, OpenAI, and Gemini. Client can pick one or 
    more LLM APIs by including `@<LLM API name>`, e.g. `@openai`, `@anthropic`,
    `@gemini`. No-op if no relevant APIs are found in prompt.

    Note that Errors from the underlying APIs are treated as normal LLM response
    text, so this method is fail-open wrt underlying LLM API failures.
    '''
    # Query LLM APIs in parallel.
    llm_apis = [
      self.llm_apis[llm_api]
      for llm_api in self.llm_apis.keys()
      if llm_api in prompt
    ]
    queries_coroutines = [
      self._single_llm_call(llm_api, prompt, connected_grpc_channels_copy) 
      for llm_api in llm_apis
    ]
    await asyncio.gather(*queries_coroutines)
