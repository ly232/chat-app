from client import chat_client
from protos.generated_pb2 import chat_service_pb2
from protos.generated_pb2 import chat_service_pb2_grpc
from server import chat_server
from threading import Thread

import asyncio
import grpc
import logging
import os
import time
import unittest

# import pdb; pdb.set_trace()

class ChatServerThread(Thread):
  '''Thread to run chat server off of the main test thread.

  This is necessary because we cannot block the main thread from running the
  actual test. The chat server must run with asyncio, which brings additional
  challenges in gracefully terminating the service at the end of each test case.
  We do this by running 2 coroutines in parallel:
  - _check_termination periodically checks for termination condition.
  - _run_server_and_check_termination kicks off the server run coroutine and
    the _check_termination coroutine, using asynio.gather() to run both
    concurrently (cascading awaits won't work as one will block the other).
  '''

  def __init__(self):
    Thread.__init__(self, name='chat-server')
    self.stop = False
    self.chat_service = None

  async def _check_termination(self):
    while True:
      if not self.stop:
        await asyncio.sleep(0.1)
      else:
        await self.chat_service.Shutdown()
        break

  async def _run_server_and_check_termination(self):
    self.chat_service = chat_server.ChatService()
    await asyncio.gather(self.chat_service.Serve(), self._check_termination())

  def run(self):
    asyncio.run(self._run_server_and_check_termination())

  def shutdown(self):
    self.stop = True

class ChatClientThread(Thread):
  def __init__(self, client_id, messages):
    Thread.__init__(self, name=f'chat-client-{client_id}')
    self.client_id = client_id
    self.client = chat_client.ChatClient(client_id)
    self.messages = messages
    self.received = []

  async def _generate_messages(self, unused):
    # Initiate a dummy empty message to establish the connection. Without this,
    # the client won't establish a connection to server just yet, which means
    # the very first message will not be seen by other clients.
    yield chat_service_pb2.ChatMessage(sender_id=self.client_id)

    for message in messages:
      yield chat_service_pb2.ChatMessage(
        content=message, sender_id=self.client_id)

  async def _receive_messages(self, stream, unused):
    print(type(stream))
    async for response in stream:
      print(f'received: {response}')
      if response.sender_id != self.client_id:
        self.received.append(response.content)
      if response.content == 'quit':
        return

  def run(self):
    asyncio.run(
      self.client.run(
        self._generate_messages,
        self._receive_messages))


class IntegrationTest(unittest.TestCase):

  def simulate_client(self, client_id, messages=None):
    '''Test util to simulate a client sending n messages
    '''
    def requests_generator():
      for i in range(3):
        yield chat_service_pb2.ChatMessage(
          sender_id=client_id,
          content=f'message {i}')
    if not messages:
      messages = requests_generator

    channel = grpc.insecure_channel('localhost:50051')
    stub = chat_service_pb2_grpc.ChatServiceStub(channel)
    stream = stub.Chat(messages())
    # Note:
    # - `channel` is of type `grpc._channel.Channel`.
    # - `stream` is of type `_MultiThreadedRendezvous`.
    return channel, stream

  def setUp(self):
    self.server = ChatServerThread()
    self.server.start()

  def tearDown(self):
    self.server.shutdown()
    self.server.join()

  def test_single_client(self):
    channel, stream = self.simulate_client('client1')
    self.assertEqual(list(stream), [
      chat_service_pb2.ChatMessage(
        sender_id='client1',
        content='message 0'),
      chat_service_pb2.ChatMessage(
        sender_id='client1',
        content='message 1'),
      chat_service_pb2.ChatMessage(
        sender_id='client1',
        content='message 2'),
    ])
    channel.close()

  def test_multi_clients(self):
    channel1, stream1 = self.simulate_client('client1')
    channel2, stream2 = self.simulate_client('client2')

    responses1 = list(stream1)
    responses2 = list(stream2)

    self.assertIn(
      chat_service_pb2.ChatMessage(
        sender_id='client1',
        content='message 0'),
      responses1)
    self.assertIn(
      chat_service_pb2.ChatMessage(
        sender_id='client1',
        content='message 1'),
      responses1)
    self.assertIn(
      chat_service_pb2.ChatMessage(
        sender_id='client1',
        content='message 2'),
      responses1)

    self.assertIn(
      chat_service_pb2.ChatMessage(
        sender_id='client2',
        content='message 0'),
      responses2)
    self.assertIn(
      chat_service_pb2.ChatMessage(
        sender_id='client2',
        content='message 1'),
      responses2)
    self.assertIn(
      chat_service_pb2.ChatMessage(
        sender_id='client2',
        content='message 2'),
      responses2)

    channel1.close()
    channel2.close()

  def test_gemini(self):
    '''ATTN: $GEMINI_API_KEY must be a valid environment variable.
    '''
    def gemini_generator():
      yield chat_service_pb2.ChatMessage(
        sender_id='client',
        content='@gemini when was google founded?')
    channel, stream = self.simulate_client('client', gemini_generator)
    responses = list(stream)
    gemini_responses = [r for r in responses if r.sender_id == 'Gemini']
    self.assertEqual(len(gemini_responses), 1)
    self.assertTrue('1998' in gemini_responses[0].content)
    channel.close()


if __name__ == '__main__':
  # logging.basicConfig(level=logging.INFO)
  unittest.main()
