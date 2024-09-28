from ai_agent import AiAgent
from collections import namedtuple
from protos.generated_pb2 import chat_service_pb2
from protos.generated_pb2 import chat_service_pb2_grpc
from typing import AsyncIterator

import asyncio
import grpc
import logging
import os
import time


ClientConnectionContext = namedtuple(
  'ClientConnectionContext', [
    'context', # grpc.aio.ServicerContext
    'last_update_time', # timestamp
  ])

class ChatService(chat_service_pb2_grpc.ChatServiceServicer):
  '''gRPC service impl for ChatService.
  '''
  def __init__(self):
    # Maps client ID to ClientConnectionContext.
    self._connected_grpc_channels = {}
    self.server = None

    # As per https://grpc.github.io/grpc/python/grpc_asyncio.html#grpc.aio.ServicerContext.write
    # gRPC server side context does not allow for 2 concurrent write coroutines
    # be concurrently active in the event loop. The ChatServer.Chat broadcast
    # logic is therefore error-prone to a potential race condition:
    # 1) client1 sends a message to server, server puts the reply to event loop.
    # 2) before client1 reply is flushed, client2's request comes in, which
    #    triggers a broadcast including sending client2's message to client1.
    # 3) now event loop contains 2 pending write coroutines both agains the
    #    SAME server context (aka channel) for client1, which violates the
    #    gRPC contract, and raises GRPC_CALL_ERROR_TOO_MANY_OPERATIONS error.
    # 
    # This set aims to solve the race condition. It simply keeps track of the
    # currently active writing channels, and writer coroutine in step 2 would
    # `await asyncio.sleep()` as long as the target channel is in this set.
    self.active_writing_channels = set()

    self.ai_agent = AiAgent(self)

  async def _broadcast(self, connected_grpc_channels_copy, request):
    # Broadcast to all other currently connected clients, and garbage-collect
    # closed clients, where we keep track of client id + timestamp when we
    # detected a closed channel.
    closed_clients = {}
    for client_id, ctx in connected_grpc_channels_copy.items():
      channel, _ = ctx.context, ctx.last_update_time
      # channel is of type grpc.aio.ServicerContext.
      while channel in self.active_writing_channels:
        await asyncio.sleep(0.1)
      if not channel.done():
        self.active_writing_channels.add(channel)
        try:
          await channel.write(request)
        except Exception:
          logging.info(f'Channel {channel} was recently closed. Skipping')
        finally:
          self.active_writing_channels.remove(channel)
      else:
        # Some other client's request_iterator has exhausted iteration. Even
        # if that other client invokes Chat again with a new request_iterator,
        # it will still be a new channel, so we can safely close this channel
        # now.
        closed_clients[client_id] = time.time()

    # There might be a subtle race condition if we only checks for client to
    # determine delete condition:
    #
    # t1: c is in closed clients, so this coroutine passes the if check but
    #     not yet deleting it.
    # t2: another coroutine initiated from c comes in, inserts c into map.
    # t3: now back to this coroutine, which will mistakenly delete the entry
    #     inserted by t2.
    #
    # One solution is to add a timestamp. Deletion only happens if the last
    # update time of c in _connected_grpc_channels  <= last read time of c
    # in closed_clients
    for client, last_read_time in closed_clients.items():
      if client in self._connected_grpc_channels and \
        last_read_time >= \
          self._connected_grpc_channels[client].last_update_time:
        del self._connected_grpc_channels[client]

  async def Chat(
    self, 
    request_iterator: AsyncIterator[chat_service_pb2.ChatMessage],
    context: grpc.aio.ServicerContext):
    async for request in request_iterator:
      logging.info(f'received chat message: {request}')

      # Keeps track of client.
      # Reset to client's latest connection. This assumes end user keeps
      # exactly one connection at any given time.
      self._connected_grpc_channels[request.sender_id] = \
        ClientConnectionContext(context, time.time())

      # Make a copy and iterate based on the copy. This ensures any other RPCs
      # will not modify the collection while it's being iterated.
      connected_grpc_channels_copy = {
        k: v for k, v in self._connected_grpc_channels.items()
      }

      # Brodcast request message to online users.
      await self._broadcast(connected_grpc_channels_copy, request)

      # Relay to LLMs.
      await self.ai_agent.query(request.content, connected_grpc_channels_copy)


  async def Serve(self, port=50051) -> None:
    self.server = grpc.aio.server()
    chat_service_pb2_grpc.add_ChatServiceServicer_to_server(self, self.server)
    self.server.add_insecure_port(f'[::]:{port}')
    await self.server.start()
    logging.info(f'Server is running on port {port}.')
    await self.server.wait_for_termination()
    logging.info(f'Shutting down server...')

  async def Shutdown(self) -> None:
    await self.server.stop(grace=None)
