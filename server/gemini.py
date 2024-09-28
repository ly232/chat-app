import aiohttp
import json
import os

import logging

URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

class GeminiRestClient:
  '''Wrapper client to call Gemini REST API.

  This is a workaround to avoid Python SDK dependency, until GCP supports it.
  '''
  def __init__(self):
    pass

  async def query(self, prompt):
    url_with_key = f"{URL}?key={GEMINI_API_KEY}"

    headers = {
      'Content-Type': 'application/json',
    }
    
    data = {
      "contents": [{
        "parts": [{"text": prompt}]
      }]
    }

    async with aiohttp.ClientSession() as session:
      async with session.post(
        url_with_key, headers=headers, json=data) as response:
        response_data = await response.json()
        # print('Status:', response.status)
        # print('Response:', json.dumps(response_data, indent=2))
        try:
          return response_data['candidates'][0]['content']['parts'][0]['text']
        except Exception as ex:
          logging.error(str(ex))
          return str(response_data)
