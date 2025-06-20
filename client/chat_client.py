'''Client-side chat app.

Note that this file is NOT deployed to GCP. It's purely for local demo purpose.

Example usage (must run under project root directory):

  python -m client.chat_client

or to connect to remote server in GCP:

  python -m client.chat_client --remote=true
'''

from .dao import DataAccessObject
from protos.generated_pb2 import chat_service_pb2
from protos.generated_pb2 import chat_service_pb2_grpc

import argparse
import grpc
import asyncio
import os

class ChatClient:
  '''A simple chat client.
  '''

  def __init__(self, client_id, remote=False):
    '''Initializes the chat client.

    Args:
    `client_id` (str): client id to identify to the server. Note that server
      will use the same gRPC connection for the same client id.
    `remote` (bool): whether to connect to remote GCP server.
    '''
    self._client_id = client_id
    self._remote = remote
    self._dao = DataAccessObject()

  async def run(self):
    '''Start running the client.

    Args:
    `generate_messages` (function): an async generator that yields messages that
      this client intends to send. The function takes in a single str argument
      `client_id`.
    `receive_messages` (function): a coroutine that takes in an async generator
      and a client id, and defines processing logic upon each value yielded by
      the async generator.
    '''

    # Print chat history for last 1 day.
    history = await self._dao.list_messages(last_n_days=1)
    print(f'== Chat history from past 1 day ==')
    print('\n\n'.join([
      f'{message.user_name}: {message.message}' for message in history]))
    print('== End of chat history ==')

    with open('server.crt', 'rb') as f:
      trusted_certs = f.read()
    creds = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
    if self._remote:
      chat_app_server_spec = 'chat-app-631248462212.us-central1.run.app:443'
      print(f'connecting to {chat_app_server_spec}')
      # Note: must use secure_channel, even if server uses add_insecure_port.
      # Using insecure_channel leads to "failed to connect to all addresses; last 
      # error: UNAVAILABLE: ...: Socket closed".
      channel = grpc.aio.secure_channel(chat_app_server_spec, creds)
    else:
      print(f'connecting to localhost:50051')
      channel = grpc.aio.secure_channel('localhost:50051', creds)

    async with channel:
      stub = chat_service_pb2_grpc.ChatServiceStub(channel)

      # Open the chat stream.
      stream = stub.Chat(self.generate_messages(self._client_id))

      # Create a coroutine task for receiving messages.
      receive_task = asyncio.create_task(
        self.receive_messages(stream, self._client_id))

      # Awaiting on the coroutine in event loop. If `stream` receives a message,
      # event loop will execute the `receive_messages` callback, otherwise the
      # coroutine will be placed to the end of the event loop to yield execution
      # to other coroutines (namely, the main coroutine).
      await receive_task

  #
  # Define generator and coroutine for this particular chat client app.
  #
  async def generate_messages(self, client_id):
    # Initiate a dummy empty message to establish the connection. Without this,
    # the client won't establish a connection to server just yet, which means
    # the very first message will not be seen by other clients.
    yield chat_service_pb2.ChatMessage(sender_id=client_id)

    # Now interactively awaits user to enter next messasge.
    while True:
      message_content = input(f'{client_id}: ')
      await self._dao.write_message(
        user_name=client_id, message=message_content)
      yield chat_service_pb2.ChatMessage(
        content=message_content, sender_id=client_id)
      # Sleep a bit to give event loop a chance to display any pending messages.
      await asyncio.sleep(0.1)

  async def receive_messages(self, stream, client_id):
    async for response in stream:
      if response.content and client_id != response.sender_id:
        print(f'\n{response.sender_id}: {response.content}\n=====\n')
        await self._dao.write_message(
          user_name=response.sender_id, message=response.content)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Chat app client.")
  parser.add_argument(
    '--remote', type=bool, help='Whether to wire to remote GCP server.')
  args = parser.parse_args()

  client_id = input("Enter your client ID: ")
  chat_client = ChatClient(client_id, args.remote)
  try:
    asyncio.run(chat_client.run())
  except KeyboardInterrupt:
    print("\nChat ended.")
