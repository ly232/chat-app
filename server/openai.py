from server.llm_api_base import LlmApiBase

import os

URL = 'https://api.openai.com/v1/responses'
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
MODEL = 'gpt-3.5-turbo'

'''Wrapper client to call OpenAI REST API.

Using CURL instead of Python SDK to minimize risks in cloud platform
deployment constraints (e.g. GCP cannot run many Python SDKs, as of 2024).

Documentation: https://platform.openai.com/docs/api-reference/introduction.
'''
class OpenAiRestClient(LlmApiBase):

  def __init__(self):
    super().__init__(
      name='OpenAI',
      url=URL,
      api_key=OPENAI_API_KEY,
      headers={
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json',
      },
      prompt_to_data=lambda prompt: {
        'model': MODEL,
        'input': prompt,
      },
      response_extraction_callbck=lambda response_data: \
        response_data['output'][0]['content'][0]['text']
    )
