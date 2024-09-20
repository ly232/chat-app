from server import chat_server

import asyncio
import grpc
import logging
import os

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  asyncio.run(chat_server.ChatService().Serve(port=os.environ.get('PORT', 50051)))
