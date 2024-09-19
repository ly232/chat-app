from proto.generated_pb2 import chat_service_pb2
from proto.generated_pb2 import chat_service_pb2_grpc
from typing import AsyncIterator

import asyncio
import grpc
import logging

class ChatService(chat_service_pb2_grpc.ChatServiceServicer):
  '''gRPC servi e impl for ChatService.
  '''
  def __init__(self):
    # Maps client ID to grpc.aio.ServicerContext.
    self._connected_grpc_channels = {}

  async def Chat(
    self, 
    request_iterator: AsyncIterator[chat_service_pb2.ChatMessage],
    context: grpc.aio.ServicerContext,
  ) -> AsyncIterator[chat_service_pb2.ChatMessage]:
    async for request in request_iterator:
      logging.info(f'received chat message: {request}')

      # Keeps track of client.
      # Reset to client's latest connection. This assumes end user keeps
      # exactly one connection at any given time.
      self._connected_grpc_channels[request.sender_id] = context

      # Broadcast to all other currently connected clients, and garbage-collect
      # closed clients.
      closed_clients = []
      for client_id, channel in self._connected_grpc_channels.items():
        if not channel.done():
          await channel.write(request)
          if '@AiAgent' in request.content:
            # TODO: interact with AI Agent.
            pass
        else:
          closed_clients.append(client_id)
      for client in closed_clients:
        del self._connected_grpc_channels[client]

async def Serve(port=50051) -> None:
  server = grpc.aio.server()
  chat_service_pb2_grpc.add_ChatServiceServicer_to_server(
    ChatService(), server)
  server.add_insecure_port(f'[::]:{port}')
  await server.start()
  logging.info(f'Server is running on port {port}.')
  await server.wait_for_termination()
