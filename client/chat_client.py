'''Client-side chat app.

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
  while True:
    message_content = input(f'{client_id}: ')
    yield chat_service_pb2.ChatMessage(content=message_content, sender_id=client_id)

async def receive_messages(stream, client_id):
  async for response in stream:
    if response.content and client_id != response.sender_id:
      print(f'Received: {response.content} from {response.sender_id}')

async def run(client_id, remote):

  with open('roots.pem', 'rb') as f:
    creds = grpc.ssl_channel_credentials(f.read())
  if remote:
    assert 'CHAT_APP_SERVER_SPEC' in os.environ, 'Please set env var CHAT_APP_SERVER_SPEC.'
    print(f'connecting to {os.environ.get('CHAT_APP_SERVER_SPEC')}')
    channel = grpc.aio.secure_channel(os.environ.get('CHAT_APP_SERVER_SPEC'), creds)
  else:
    print(f'connecting to localhost:50051')
    channel = grpc.aio.insecure_channel('localhost:50051')

  async with channel:
    stub = chat_service_pb2_grpc.ChatServiceStub(channel)

    # Open the chat stream.
    stream = stub.Chat(generate_messages(client_id))

    # Create a task for receiving messages
    receive_task = asyncio.create_task(receive_messages(stream, client_id))

    # Send messages
    await receive_task

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Chat app client.")
  parser.add_argument('--remote', type=bool, help='Whether to wire to remote GCP server.')
  args = parser.parse_args()

  client_id = input("Enter your client ID: ")
  try:
    asyncio.run(run(client_id, args.remote))
  except KeyboardInterrupt:
    print("\nChat ended.")
