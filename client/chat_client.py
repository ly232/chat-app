'''Client-side chat app.

Note that this file is NOT deployed to GCP. It's purely for local demo purpose.

Example usage (must run under project root directory):

  python -m client.chat_client

or to connect to remote server in GCP:

  python -m client.chat_client --remote=true
'''

from proto.generated_pb2 import chat_service_pb2
from proto.generated_pb2 import chat_service_pb2_grpc

import argparse
import grpc
import asyncio
import os

async def generate_messages(client_id):
  # Initiate a dummy empty message to establish the connection. Without this,
  # the client won't establish a connection to server just yet, which means the
  # very first message will not be seen by other clients.
  yield chat_service_pb2.ChatMessage(sender_id=client_id)

  # Now interactively awaits user to enter next messasge.
  while True:
    message_content = input(f'{client_id}: ')
    yield chat_service_pb2.ChatMessage(
      content=message_content, sender_id=client_id)
    # Sleep a bit to give event loop a chance to display any pending messages.
    await asyncio.sleep(0.1)

async def receive_messages(stream, client_id):
  async for response in stream:
    if response.content and client_id != response.sender_id:
      print(f'Received: {response.content} from {response.sender_id}')

async def run(client_id, remote):
  creds = grpc.ssl_channel_credentials()
  if remote:
    assert 'CHAT_APP_SERVER_SPEC' in os.environ, \
      'Please set env var CHAT_APP_SERVER_SPEC.'
    print(f'connecting to {os.environ.get('CHAT_APP_SERVER_SPEC')}')
    # Note: must use secure_channel, even if server uses add_insecure_port.
    # Using insecure_channel leads to "failed to connect to all addresses; last 
    # error: UNAVAILABLE: ...: Socket closed".
    channel = grpc.aio.secure_channel(
      os.environ.get('CHAT_APP_SERVER_SPEC'), creds)
  else:
    print(f'connecting to localhost:50051')
    channel = grpc.aio.insecure_channel('localhost:50051')

  async with channel:
    stub = chat_service_pb2_grpc.ChatServiceStub(channel)

    # Open the chat stream.
    stream = stub.Chat(generate_messages(client_id))

    # Create a coroutine task for receiving messages
    receive_task = asyncio.create_task(receive_messages(stream, client_id))

    # Awaiting on the coroutine in event loop. If `stream` receives any message,
    # event loop will execute the `receive_messages` callback, otherwise the
    # coroutine will be placed to the end of the event loop to yield execution
    # to other coroutines (namely, the main coroutine).
    await receive_task

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Chat app client.")
  parser.add_argument(
    '--remote', type=bool, help='Whether to wire to remote GCP server.')
  args = parser.parse_args()

  client_id = input("Enter your client ID: ")
  try:
    asyncio.run(run(client_id, args.remote))
  except KeyboardInterrupt:
    print("\nChat ended.")
