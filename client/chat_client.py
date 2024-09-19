from proto.generated_pb2 import chat_service_pb2
from proto.generated_pb2 import chat_service_pb2_grpc

import grpc
import asyncio

async def generate_messages(client_id):
  while True:
    message_content = input(f'{client_id}: ')
    yield chat_service_pb2.ChatMessage(content=message_content, sender_id=client_id)

async def receive_messages(stream, client_id):
  async for response in stream:
    if response.content and client_id != response.sender_id:
      print(f'Received: {response.content} from {response.sender_id}')

async def run(client_id):
  async with grpc.aio.insecure_channel('localhost:50051') as channel:
    stub = chat_service_pb2_grpc.ChatServiceStub(channel)

    # Open the chat stream.
    stream = stub.Chat(generate_messages(client_id))

    # Create a task for receiving messages
    receive_task = asyncio.create_task(receive_messages(stream, client_id))

    # Send messages
    await receive_task

if __name__ == '__main__':
  client_id = input("Enter your client ID: ")
  try:
    asyncio.run(run(client_id))
  except KeyboardInterrupt:
    print("\nChat ended.")
