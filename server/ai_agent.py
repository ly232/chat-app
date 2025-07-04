from anthropic import AnthropicRestClient
from gemini import GeminiRestClient
from openai import OpenAiRestClient
from protos.generated_pb2 import chat_service_pb2
from mcp_servers.mcp_server_connector import McpServerConnector
from server.llm_mesage import LllMessage
from typing import Any, List

import asyncio
import logging


class AiAgent:
  '''Proxy to talk to LLM APIs.
  '''

  def __init__(self, chat_server):
    self.chat_server = chat_server
    tools = [
      tool_and_server.tool 
      for tool_and_server in 
        chat_server.mcp_server_connector.get_available_tools().values()
    ]
    mcp_tools = [
      {
          "name": tool.name,
          "description": tool.description,
          "input_schema": tool.inputSchema
      }
      for tool in tools
    ]
    self.llm_apis = {
      '@google': GeminiRestClient(ai_agent=self),
      '@gemini': GeminiRestClient(ai_agent=self),
      '@anthropic': AnthropicRestClient(mcp_tools=mcp_tools, ai_agent=self),
      '@claude': AnthropicRestClient(mcp_tools=mcp_tools, ai_agent=self),
      '@openai': OpenAiRestClient(ai_agent=self),
    }
    # Tracks all user/llm interactions, including MCP messages.
    self.message_history: List[LllMessage] = []

  '''Internal method to first invoke llm api, then broadcast to channel.'''
  async def _single_llm_call(self, llm_api, prompt, channel):
    reply = await llm_api.query(prompt)
    await self.chat_server._broadcast(
        channel,
        chat_service_pb2.ChatMessage(
          sender_id=llm_api.name,
          content='\n\n' + reply if reply else '' + '\n\n'))
    
  async def call_mcp_tools(self, tool_name: str, arguments: dict) -> Any:
    '''Proxy to invoke MCP tools registered in MCP server connector.'''
    results = await self.chat_server.mcp_server_connector.call_mcp_tools(
      tool_name, arguments)
    return results

  async def query(self, prompt, connected_grpc_channels_copy):
    '''Sends prompt to relevant LLM APIs.

    Intends to support Anthropic, OpenAI, and Gemini. Client can pick one or 
    more LLM APIs by including `@<LLM API name>`, e.g. `@openai`, `@anthropic`,
    `@gemini`. No-op if no relevant APIs are found in prompt.

    Note that Errors from the underlying APIs are treated as normal LLM response
    text, so this method is fail-open wrt underlying LLM API failures.
    '''
    self.message_history.append(LllMessage('user', prompt))
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
