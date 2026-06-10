import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    # ... (остальной код без изменений) ...
    # Discord
    BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")
    
    # Bot Settings
    PREFIX = "!"
    
    # YouTube / Cookies
    COOKIES_FILE = "cookies.txt"
    
    # FFmpeg Options
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    
    # yt-dlp Options
    YDL_OPTIONS = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': False, # Разрешаем плейлисты
        'extract_flat': 'in_playlist', # Не извлекаем полную инфу сразу для плейлистов (ускорение)
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'cookiefile': COOKIES_FILE
    }

# Настройка логирования
def setup_logging():
    # Создаем директорию для логов если её нет
    os.makedirs("logs", exist_ok=True)
    
    # Ротация логов: макс 5 МБ, хранить 5 последних файлов
    file_handler = RotatingFileHandler(
        "logs/bot.log", 
        maxBytes=5*1024*1024, 
        backupCount=5, 
        encoding="utf-8"
    )
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
    # Отключаем лишний шум от библиотек
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

