from server import chat_server

import asyncio
import logging
import os

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  asyncio.run(chat_server.Serve(port=os.environ.get('PORT', 50051)))