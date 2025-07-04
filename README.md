# Chat app with AI agent

## Overview

A chat app that leverages gRPC's bi-di streaming capability to broadcast to all
online clients & AI chatbots.

Typical user journeys:
1.  N users are logged in.
2.  One user types some message. This message is transmitted to server.
3.  Server broadcasts the message to all N-1 online users.
4.  Anyone can optionally type `@<AI chatbot>` to interact with AI chatbots.
    For example, `@gemini`, `@anthropic`, ...

## Demo

![Screenshot](demo.png)

![Screencast](demo.gif)

## Architecture

### Class design

```mermaid
classDiagram
    class ChatServer {
        -McpServerConnector mcp_server_connector
        -List~AiAgent~ ai_agents
        -Set~Client~ active_clients
        +Serve() void
        +BroadcastMessage(Message message) void
        +HandleClientConnection(Client client) void
        +ProcessAiChatRequest(AiChatRequest request) AiChatResponse
    }

    class McpServerConnector {
        -List~McpServer~ servers
        -List~McpTool~ tools
        +connect_to_servers() List~McpTool~
        +initialize() void
        +get_available_tools() List~McpTool~
        +execute_tool(String tool_name, dict params) ToolResult
    }

    class ChatClient {
        -DatabaseManager db_manager
        -Channel grpc_channel
        -Stream message_stream
        +connect_to_server() void
        +send_message(Message message) void
        +receive_messages() Stream~Message~
        +handle_ai_response(AiResponse response) void
    }

    class AiAgent {
        -String agent_name
        -ApiClient api_client
        -List~McpTool~ mcp_tools
        +process_message(Message message) AiResponse
        +get_agent_name() String
        +initialize_with_tools(List~McpTool~ tools) void
    }

    class AnthropicRestClient {
        -String api_key
        -List~McpTool~ mcp_tools
        -String endpoint
        +make_request(String prompt, List~McpTool~ tools) ApiResponse
        +handle_tool_use(ToolUse tool_use) ToolResult
    }

    class GeminiRestClient {
        -String api_key
        -List~McpTool~ mcp_tools
        -String endpoint
        +make_request(String prompt, List~McpTool~ tools) ApiResponse
        +handle_tool_use(ToolUse tool_use) ToolResult
    }

    class DatabaseManager {
        -String db_path
        -Connection connection
        +save_message(Message message) void
        +get_chat_history() List~Message~
        +search_messages(String query) List~Message~
        +initialize_db() void
    }

    class Message {
        -int id
        -String sender
        -String content
        -datetime timestamp
        -MessageType message_type
        +to_protobuf() MessageProto
        +from_protobuf(MessageProto proto) Message
    }

    class MessageProto {
        +int32 id
        +string sender
        +string content
        +int64 timestamp
        +MessageType type
    }

    class AiChatRequest {
        -Message message
        -String target_agent
        -String context
        +to_protobuf() AiChatRequestProto
    }

    class AiChatResponse {
        -String response_content
        -String agent_name
        -List~ToolResult~ tool_results
        +to_protobuf() AiChatResponseProto
    }

    class McpTool {
        -String name
        -String description
        -dict parameters
        +execute(dict params) ToolResult
        +to_api_format() dict
    }

    class ToolResult {
        -String tool_name
        -any result
        -bool success
        -String error_message
    }

    class GitInfoTool {
        +get_git_status() GitStatus
        +get_commit_history() List~Commit~
        +execute(dict params) ToolResult
    }

    ChatServer --> ChatClient
    ChatServer --> McpServerConnector
    ChatServer --> AiAgent
    ChatServer --> Message
    
    ChatClient --> DatabaseManager
    ChatClient --> Message
    
    AiAgent --> AnthropicRestClient
    AiAgent --> GeminiRestClient
    AiAgent --> McpTool
    
    AnthropicRestClient --> AiChatRequest
    AnthropicRestClient --> AiChatResponse
    GeminiRestClient --> AiChatRequest
    GeminiRestClient --> AiChatResponse
    
    McpServerConnector --> McpTool
    McpServerConnector --> GitInfoTool
    
    DatabaseManager --> Message
    
    Message --> MessageProto
    AiChatRequest --> AiChatResponse
    
    McpTool --> ToolResult
    GitInfoTool --> McpTool
```

### gRPC vs. Web Socket

Unlike a typical chat app where it heavily leverages web sockets, this chat app
intentionally uses gRPC bi-di streaming for the following reasons:

1.  Language-agnostic stub codegen helps to reduce boilerplates.
2.  Transferring protobuf rather than json requires less network bandwidth.
3.  Protobuf enforces strong typing.

### Database choice

We use sqlite on the client side only. This ensures remote server's sole
responsibilities are (a) message broadcasting, and (b) AI chatbot interactions,
so that we don't have to distribute AI chatbot's API keys to clients. And at the
same time, chat histories are entirely local, easy to search, and preserves
privacy.

We chose sqlite instead of other database soluions mostly for its simple Python
APIs and mature ecosystem. We also use sqlalchemy for db adapter. All APIs use
the asyncio version to stay compatible with the rest of the async chat app.

Local database can be accessed as follows:

```
sqlite3 chat-app-client-local.db

> SELECT * FROM Message;
```

### MCP Integration

1. `server/mcp_servers/mcp_server_connector.py` takes care of MCP server
   bootstrapping and connection. Currently it oly connects to a demo server that
   gets local git commit status. By the end of `connect_to_servers()` call, it's
   ready to return the list of available MCP tools.
2. `McpServerConnector` is a member of `ChatServer`, which gets initialized
   *right after* `ChatServer.Serve()` is called. This is because
   `McpServerConnector` initialization (i.e. call `connect_to_servers()`) is
   async and cannot be invoked inside `__init__`.
3. The MCP tools availble is static across the session, so they can be passed
   as constructor arguments to the various AI agents. In `AiAgent`, we pass
   `mcp_tools` to underlying LLM API clients that support MCP tooling. For
   example, `AnthropicRestClient` takes in `mcp_tools` and use it as a request
   field `tools = mcp_tools` when making the HTTPS call.
4. LLM API follows MCP protocol to return content with `type == "tool_use"`.
   Then it's back to the agent's implementation responsibility to invoke the
   relevant tools requested by the LLM API.
   * TODO: think through the design - this may be anthoter bidi stream.

## Local development

Local setup:

```
uv venv
uv pip install -r requirements.txt
source .venv/bin/activate
source ~/.bashrc
```

Start server:

```
uv run chat_server_main.py
```

Start client:

```
# Terminal 1:
uv run -m client.chat_client

# Terminal 2:
uv run -m client.chat_client
```

## Security

SSL/TLS establishes a trusted channel between client and server. Normally for browser-based apps, it's recommended to have a trusted CA issue the cert. But (a) it costs money, and (b) in this chat app, both client and server are self-owned and client is a commandline tool. So we'll opt for a self-served SSL/TLS generated cert. Setting up SSL/TLS enables e2e encryption to protect against man-in-the-middle attacks.

```
# Generate a private key
openssl genpkey -algorithm RSA -out server.key -aes256

# To remove password:
openssl rsa -in server.key -out server.key

# Generate a certificate signing request (CSR)
# Remember to set:
# Common Name (e.g. server FQDN or YOUR name) []:localhost
openssl req -new -key server.key -out server.csr

# Create the self-signed certificate
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
```

## CI/CD

Chat server is deployed on GCP Cloud Run.

`git push -u origin main` will trigger a Cloud Build.

Deploy local repo to GCP:

```
gcloud config set project chat-app-436116

gcloud run deploy chat-app --source .
```

## Future ideas

### Features

*  MCP integration.
*  Access control.
*  Mobile app & web app.
*  Multi-media support.

### Infrastructure

*  GitHub Action for CI/CD.
*  Kubernetes migration.
*  Prober test.
*  Load test.
