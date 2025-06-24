from server.llm_api_base import LlmApiBase
from typing import List, Dict

import os

URL = 'https://api.anthropic.com/v1/messages'
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
MODEL = 'claude-opus-4-20250514'
MAX_TOKENS = 1024

'''Wrapper client to call Anthropic REST API.

Using CURL instead of Python SDK to minimize risks in cloud platform
deployment constraints (e.g. GCP cannot run many Python SDKs, as of 2024).

Documentation: https://docs.anthropic.com/en/api/overview.
'''
class AnthropicRestClient(LlmApiBase):

  def __init__(self, mcp_tools: List[Dict[str, str]]):
    super().__init__(
      name='Claude',
      url=URL,
      api_key=ANTHROPIC_API_KEY,
      headers={
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      prompt_to_data=lambda prompt: {
        'model': MODEL,
        'max_tokens': MAX_TOKENS,
        'tools': mcp_tools,
        'messages': [
          {'role': 'user', 'content': prompt}
        ]
      },
      response_extraction_callbck=self.response_extraction_callbck
    )

  def response_extraction_callbck(self, response_data):
    print(f'!!!!! RESPONSE: {response_data}')
    # return response_data['content'][0]['text']

    reply_message = None
    for content in response_data['content']:
      if content['type'] == 'message':
        reply_message = content['text']
      if content['type'] == 'tool_use':
        # TODO: make MCP tool call.
        pass
    return reply_message
