from dataclasses import dataclass

@dataclass
class LllMessage:
  role: str = 'user'  # Examples: 'user', 'assistant'
  content: str = ''
