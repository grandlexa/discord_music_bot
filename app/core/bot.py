import discord
from discord.ext import commands
from app.core.config import Config
import logging

class MusicBot(commands.Bot):
    def __init__(self):
        # Настройка интентов
        intents = discord.Intents.default()
        intents.message_content = True  # Для чтения команд
        intents.voice_states = True     # Для отслеживания голосовых каналов
        
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            description="Discord Music Bot Trae"
        )
        self.logger = logging.getLogger("bot")

    async def setup_hook(self):
        self.logger.info("Initializing bot...")
        # Загружаем коги
        try:
            await self.load_extension("app.commands.music")
            self.logger.info("Loaded extension: app.commands.music")
        except Exception as e:
            self.logger.error(f"Failed to load extension app.commands.music: {e}")

    async def on_ready(self):
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        self.logger.info('------')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return # Игнорируем неизвестные команды
        
        self.logger.error(f'Error in command {ctx.command}: {error}')
        await ctx.send(f'❌ Произошла ошибка: {str(error)}')
