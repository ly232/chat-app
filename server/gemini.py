from server.llm_api_base import LlmApiBase

import os

URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

'''Wrapper client to call Gemini REST API.

Using CURL instead of Python SDK to minimize risks in cloud platform
deployment constraints (e.g. GCP cannot run many Python SDKs, as of 2024).

Documentation: https://ai.google.dev/gemini-api/docs.
'''
class GeminiRestClient(LlmApiBase):

  def __init__(self):
    super().__init__(
      name='Gemini',
      url=f"{URL}?key={GEMINI_API_KEY}",
      api_key=GEMINI_API_KEY,
      headers={
        'Content-Type': 'application/json',
      },
      prompt_to_data=lambda prompt: {
        "contents": [{
          "parts": [{"text": prompt}]
        }]
      },
      response_extraction_callbck=lambda response_data: \
        response_data['candidates'][0]['content']['parts'][0]['text']
    )
