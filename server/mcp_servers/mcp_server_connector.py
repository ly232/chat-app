from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List

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

class McpServerConnector:
    '''Class that manages connects to MCP servers.'''

    def __init__(self):
        self.server_configs = SERVER_CONFIGS['mcpServers']
        self.exit_stack = AsyncExitStack()
        self.sessions: List[ClientSession] = []
        self.available_tools = []

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
        self.sessions.append(session)

        # List available tools.
        response = await session.list_tools()
        print(f'Tools: {response.tools}, from server {server_name}')
        self.available_tools.extend(response.tools)

    def get_available_tools(self):
        return self.available_tools
