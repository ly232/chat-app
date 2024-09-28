from anthropic import AsyncAnthropic
from openai import OpenAI
from protos.generated_pb2 import chat_service_pb2

import anthropic
import google.generativeai as gemini
import logging
import os

gemini.configure(api_key=os.environ["GEMINI_API_KEY"])
GEMINI_API_CLIENT = gemini.GenerativeModel("gemini-1.5-flash")

OPENAI_API_CLIENT = OpenAI()

ANTHROPIC_API_CLIENT = AsyncAnthropic(
    # This is the default and can be omitted
    api_key=os.environ.get('ANTHROPIC_API_KEY'),
)

class AiAgent:
  '''Proxy to talk to LLM APIs.
  '''

  def __init__(self, chat_server):
    self.chat_server = chat_server

  async def query(self, prompt, connected_grpc_channels_copy):
    '''Sends prompt to relevant LLM APIs.

    Currently supports Anthropic, OpenAI, and Gemini. Client can pick one or 
    more LLM APIs by including `@<LLM API name>`, e.g. `@openai`, `@anthropic`,
    `@gemini`. No-op if no relevant APIs are found in prompt.

    Note that Errors from the underlying APIs are treated as normal LLM response
    text, so this method is fail-open wrt underlying LLM API failures.
    '''
    if '@gemini' in prompt:
      try:
        # TODO: if Gemini doesn't offer async API, run this in a separate
        # executor to avoid blocking main thread.
        gemini_response = GEMINI_API_CLIENT.generate_content(prompt)
        reply = gemini_response.text
      except Exception as ex:
        logging.error(f'Gemini failed: {ex}')
        reply = str(ex)
      finally:
        await self.chat_server._broadcast(
          connected_grpc_channels_copy,
          chat_service_pb2.ChatMessage(
            sender_id='Gemini',
            content='\n\n' + reply + '\n\n'))

    if '@openai' in prompt:
      try:
        openai_response = OPENAI_API_CLIENT.chat.completions.create(
            messages=[{
                "role": "OpenAI",
                "content": prompt,
            }],
            model="gpt-4o-mini",
        )
        reply = str(openai_response)
      except Exception as ex:
        logging.error(f'OpenAI failed: {ex}')
        reply = str(ex)
      finally:
        await self.chat_server._broadcast(
          connected_grpc_channels_copy,
          chat_service_pb2.ChatMessage(
            sender_id='OpenAI',
            content='\n\n' + reply + '\n\n'))

    if '@anthropic' in prompt:
      try:
        anthropic_response = await ANTHROPIC_API_CLIENT.messages.create(
            max_tokens=1024,
            messages=[
                {
                    "role": "Anthropic Claude",
                    "content": prompt,
                }
            ],
            model="claude-3-opus-20240229",
        )
        reply = anthropic_response.content
      except anthropic.BadRequestError as ex:
        logging.error(f'Anthropic failed: {ex}')
        reply = ex.message
      finally:
        await self.chat_server._broadcast(
          connected_grpc_channels_copy,
          chat_service_pb2.ChatMessage(
            sender_id='Anthropic Claude',
            content='\n\n' + reply + '\n\n'))
