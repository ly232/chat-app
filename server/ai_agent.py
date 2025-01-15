from gemini import GeminiRestClient
from protos.generated_pb2 import chat_service_pb2

import logging


class AiAgent:
  '''Proxy to talk to LLM APIs.
  '''

  def __init__(self, chat_server):
    self.chat_server = chat_server
    self.gemini_client = GeminiRestClient()

  async def query(self, prompt, connected_grpc_channels_copy):
    '''Sends prompt to relevant LLM APIs.

    Intends to support Anthropic, OpenAI, and Gemini. Client can pick one or 
    more LLM APIs by including `@<LLM API name>`, e.g. `@openai`, `@anthropic`,
    `@gemini`. No-op if no relevant APIs are found in prompt.

    Currently supports:
    - Gemini

    Note that Errors from the underlying APIs are treated as normal LLM response
    text, so this method is fail-open wrt underlying LLM API failures.
    '''
    if '@gemini' in prompt:
      reply = await self.gemini_client.query(prompt)
      await self.chat_server._broadcast(
        connected_grpc_channels_copy,
        chat_service_pb2.ChatMessage(
          sender_id='Gemini',
          content='\n\n' + reply + '\n\n'))
