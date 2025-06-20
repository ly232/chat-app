'''DDL to set up metadata database.
'''

from .schema import Base
from contextlib import asynccontextmanager
from sqlalchemy.orm.session import Session
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

import logging

# Hide SQL SELECT, INSERT, etc. statements (sqlalchemy.engine) from stdout.
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

#
# Connection setups.
#

# Create async engine.
engine = create_async_engine(
    "sqlite+aiosqlite:///./chat-app-client-local.db",
)

# SessionLocal for creating database session for each request
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)

# Session factory method.
@asynccontextmanager
async def get_db():
    '''Opens a db session and returns session as an async context manager.
    
    Client should use `async with` for RAII.
    '''

    # Create the tables in the database. This is idempotent so recreation is ok.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session and return as an async context manager
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
