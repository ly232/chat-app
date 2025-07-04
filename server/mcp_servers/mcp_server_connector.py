from contextlib import AsyncExitStack
from dataclasses import dataclass
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Any

import json

SERVER_CONFIGS = {
    "mcpServers": {
        "default-server": {
            "command": "uv",
            "args": [
                "run",
                "./server/mcp_servers/git_info.py"
            ],
        },
        # Another public MCP server for demo purpose.
        # "filesystem": {
        #     "command": "npx",
        #     "args": [
        #         "-y",
        #         "@modelcontextprotocol/server-filesystem",
        #         "."
        #     ]
        # },
    }
}

@dataclass
class ToolAndServerName:
    tool: types.Tool
    server_name: str

class McpServerConnector:
    '''Class that manages connects to MCP servers.'''

    def __init__(self):
        self.server_configs = SERVER_CONFIGS['mcpServers']
        self.exit_stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.available_tools = {}

    async def connect_to_servers(self):
        for server_name, server_config in self.server_configs.items():
            await self.connect_to_server(server_name, server_config)
            
    async def connect_to_server(
            self, server_name: str, server_config: dict) -> None:
        '''Connects to a single MCP server.'''

        # Initialize connection.
        server_params = StdioServerParameters(**server_config)
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await session.initialize()
        self.sessions[server_name] = session

        # List available tools.
        response = await session.list_tools()
        tools = {key: val for key, val in response}.get('tools', [])
        print('Available MCP tools:')
        for tool in tools:
            print(f'\n=====\n{tool.name}: {tool.description}\n=====\n')
        self.available_tools = {
            tool.name: ToolAndServerName(tool=tool, server_name=server_name) 
            for tool in tools
        }

    def get_available_tools(self):
        return self.available_tools
    
    async def call_mcp_tools(self, tool_name: str, arguments: dict) -> Any:
        '''Call some registered MCP tool.'''
        if tool_name not in self.available_tools:
            raise ValueError(
                f'Tool {tool_name} is not found.\n' +
                f'Available tools: {self.available_tools}')
        
        server_name = self.available_tools[tool_name].server_name
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        print(f'[McpServerConnector] mcp result: {result}')
        if not result.isError:
            return result#.structuredContent['result']
        else:
            return RuntimeError(
                f'[McpServerConnector] MCP tool call failed: {result}')



