from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Base class for defining the models
Base = declarative_base()

class Message(Base):
  '''Message table to locally persist user's chat history.'''

  __tablename__ = 'Message'

  id = Column(Integer, primary_key=True, autoincrement=True)
  user_name = Column(String, index=True)
  timestamp = Column(DateTime, index=False)
  message = Column(String, index=False)
