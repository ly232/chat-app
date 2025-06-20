from typing import List
from .database import get_db
from .schema import Message
from datetime import datetime, timedelta
from datetime import datetime
from sqlalchemy import select

class DataAccessObject:
    '''Async DAO to provide CRUD interface to database.'''

    def __init__(self):
        pass

    async def list_messages(self, last_n_days=1) -> List[Message]:
        cutoff = datetime.now() - timedelta(days=last_n_days)
        async with get_db() as session:
            response = await session.execute(
                select(Message).where(Message.timestamp >= cutoff))
            return response.scalars().all()
    
    async def write_message(self, user_name, message):
        if not message:
            return
        new_message = Message(
            user_name=user_name,
            timestamp=datetime.now(),
            message=message   
        )
        async with get_db() as session:
            session.add(new_message)
            await session.commit()
            await session.refresh(new_message)
