from proto.generated_pb2 import chat_service_pb2
from proto.generated_pb2 import chat_service_pb2_grpc
from server import chat_server
from threading import Thread

import asyncio
import grpc
import os
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
    Thread.__init__(self)
    self.stop = False
    self.chat_service = None

  async def _check_termination(self):
    while True:
      if not self.stop:
        await asyncio.sleep(1)
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

class IntegrationTest(unittest.TestCase):

  def test_single_client(self):
    t = ChatServerThread()
    t.start()
    import time
    time.sleep(1)
    t.shutdown()
    t.join()

  def test_multiple_clients(self):
    t = ChatServerThread()
    t.start()
    import time
    time.sleep(1)
    t.shutdown()
    t.join()

if __name__ == '__main__':
  unittest.main()