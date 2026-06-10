import asyncio
import sys
import os

# Добавляем корневую директорию в путь, чтобы Python видел пакет app
sys.path.append(os.getcwd())

from app.core.config import Config, setup_logging
from app.core.bot import MusicBot

async def main():
    setup_logging()
    
    bot = MusicBot()
    
    try:
        await bot.start(Config.BOT_TOKEN)
    except KeyboardInterrupt:
        await bot.close()
    except Exception as e:
        print(f"Fatal error: {e}")
        
if __name__ == "__main__":
    asyncio.run(main())
