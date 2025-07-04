from dataclasses import asdict
from server.llm_mesage import LllMessage
from server.llm_api_base import LlmApiBase
from typing import List, Dict

import mcp
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

  def __init__(self, mcp_tools: List[Dict[str, str]], ai_agent: 'AiAgent'):
    self.mcp_tools = mcp_tools
    super().__init__(
      name='Claude',
      url=URL,
      api_key=ANTHROPIC_API_KEY,
      headers={
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      prompt_to_data=lambda prompt: self._create_request_body(
         LllMessage('user', prompt)),
      response_extraction_callbck=self.response_extraction_callbck,
      ai_agent=ai_agent
    )

  def _create_request_body(self, message: LllMessage) -> dict:
     assert isinstance(message, LllMessage)
     return {
        'model': MODEL,
        'max_tokens': MAX_TOKENS,
        'tools': self.mcp_tools,
        'messages': [asdict(message)]
      }

  def _requires_mcp_tools(self, response_data) -> bool:
     return any([
        content['type'] == 'tool_use'
        for content in response_data['content']
     ])

  async def call_mcp_tools(self, response_data) -> List[mcp.types.Result]:
    tool_calls = []
    tool_call_contents = [
      content
      for content in response_data['content']
      if content['type'] == 'tool_use'
    ]
    for content in tool_call_contents:
      tool_calls.append({
                        "id": content['id'],
                        "name": content['name'],
                        "input": content['input'],
                        })
    tool_results = []
    for tool_call in tool_calls:
      try:
        print(f"Calling MCP tool: {tool_call['name']} with {tool_call['input']}")
        
        result = await self.ai_agent.call_mcp_tools(
           tool_call['name'], tool_call['input'])
        print(f'[AnthropicRestClient] MCP result: {result}')
        
        # Format result for Claude
        if hasattr(result, 'content'):
            # MCP result has content attribute
            tool_result_content = []
            for content_item in result.content:
                if content_item.type == "text":
                    tool_result_content.append({
                        "type": "text",
                        "text": content_item.text
                    })
            
            tool_results.append({
                "tool_use_id": tool_call['id'],
                "type": "tool_result",
                "content": tool_result_content
            })
        else:
            # Simple result
            tool_results.append({
                "tool_use_id": tool_call['id'],
                "type": "tool_result",
                "content": str(result)
            })
              
      except Exception as e:
          print(f"Error calling tool {tool_call['name']}: {e}")
          tool_results.append({
              "tool_use_id": tool_call['id'],
              "type": "tool_result",
              "content": f"Error: {str(e)}"
          })

      return tool_results

  async def response_extraction_callbck(self, response_data):
    print(f'!!!!! RESPONSE: {response_data}')
    self.ai_agent.message_history.append(
        LllMessage('assistant', response_data['content']))

    # Make MCP calls until no longer needed
    while self._requires_mcp_tools(response_data):
      print(f'[AnthropicRestClient] will make another mcp tool call')
      tool_results = await self.call_mcp_tools(response_data)
      # Attach conversation history
      llm_api_request_body = self._create_request_body(
         self.ai_agent.message_history[0] \
          if self.ai_agent.message_history \
          else LllMessage('user', 'See MCP tool results below'))
      if len(self.ai_agent.message_history) > 1:
        for message in self.ai_agent.message_history:
           if isinstance(message, LllMessage):
              message = asdict(message)
              assert isinstance(message, dict)
           llm_api_request_body['messages'].append(message)
      # Append latest MCP tool results.
      mcp_content = {
         'role': 'user',
         'content': tool_results
      }
      self.ai_agent.message_history.append(mcp_content)
      llm_api_request_body['messages'].append(mcp_content)
      
      print(f'~~~~~ {llm_api_request_body}')
      response_data = await super().call_llm_api(llm_api_request_body)

    # Construct response.
    reply_message = ''
    for content in response_data['content']:
      print('asdf1')
      print(content)
      if content['type'] in ('text', 'message'):
        reply_message += content['text'] + '\n'
    print(f'[AnthropicRestClient] reply_message={reply_message}, response_data={response_data}')
    return reply_message
