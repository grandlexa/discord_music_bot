import discord
import asyncio
import logging

logger = logging.getLogger("media_service")

class MediaService:
    @staticmethod
    def create_source(stream_url: str, volume: float = 1.0, start_time: int = 0) -> discord.PCMVolumeTransformer:
        """Создает аудио источник FFmpeg."""
        logger.info(f"Creating source with start_time={start_time}, url={stream_url[:50]}...")
        
        # Для HLS (m3u8) лучше использовать точный seek после -i
        is_hls = '.m3u8' in stream_url
        if is_hls:
            ffmpeg_opts = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': f'-vn -ss {start_time}'
            }
        else:
            # Быстрый seek до -i для обычных файлов
            ffmpeg_opts = {
                'before_options': f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {start_time}',
                'options': '-vn'
            }
        
        # discord.FFmpegPCMAudio автоматически ищет ffmpeg в PATH
        source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_opts)
        return discord.PCMVolumeTransformer(source, volume=volume)

    @staticmethod
    async def volume_fade(voice_client: discord.VoiceClient, start_vol: float, end_vol: float, duration: float = 3.0):
        """Плавное изменение громкости."""
        if not voice_client or not voice_client.source:
            return

        steps = int(duration * 10) # 10 шагов в секунду
        if steps == 0:
            voice_client.source.volume = end_vol
            return

        diff = end_vol - start_vol
        step_val = diff / steps
        delay = duration / steps

        current = start_vol
        for _ in range(steps):
            if not voice_client.is_playing():
                break
            current += step_val
            voice_client.source.volume = max(0.0, min(1.0, current))
            await asyncio.sleep(delay)
        
        voice_client.source.volume = end_vol

    @staticmethod
    def parse_duration(seconds: int) -> str:
        """Форматирует секунды в HH:MM:SS."""
        try:
            if seconds is None:
                return "--:--"
            seconds = int(seconds)
        except (TypeError, ValueError):
            return "--:--"
        
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
