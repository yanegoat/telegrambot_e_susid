import asyncio
import logging
from app.bot import bot
from app.db.db import Database

logger = logging.getLogger(__name__)


async def async_run():
    logger.info("Starting bot...")
    db = Database(logger)
    db.init_table()
    bot.polling()


if __name__ == "__main__":
    asyncio.run(async_run())
