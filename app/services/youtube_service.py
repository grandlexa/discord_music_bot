import asyncio
import yt_dlp
import logging
from typing import Dict, List, Optional
from app.core.config import Config

logger = logging.getLogger("youtube_service")

class YouTubeService:
    def __init__(self):
        self.ydl_opts = Config.YDL_OPTIONS

    def search_and_extract(self, query: str, requester: str) -> List[Dict]:
        """
        Ищет видео по запросу или извлекает информацию по URL.
        Возвращает список треков (словарей).
        Выполняется синхронно, поэтому должна вызываться в executor.
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Если это не URL, добавляем ytsearch:
                if not (query.startswith("http://") or query.startswith("https://")):
                    query = f"ytsearch:{query}"

                info = ydl.extract_info(query, download=False)
                
                tracks = []
                
                if 'entries' in info:
                    # Это плейлист или результат поиска
                    if query.startswith("ytsearch:"):
                        # Результат поиска - берем первый
                        if info['entries']:
                            tracks.append(self._process_track(info['entries'][0], requester))
                    else:
                        # Плейлист
                        for entry in info['entries']:
                            if entry: # entry может быть None если видео удалено
                                tracks.append(self._process_track(entry, requester))
                else:
                    # Одиночное видео
                    tracks.append(self._process_track(info, requester))
                
                return tracks
        except Exception as e:
            logger.error(f"Error extracting info for {query}: {e}")
            raise e

    def _process_track(self, info: Dict, requester: str) -> Dict:
        url = info.get('webpage_url') or info.get('original_url') or info.get('url')
        if url and not url.startswith('http'):
            url = f"https://www.youtube.com/watch?v={url}"
        thumb = info.get('thumbnail')
        vid = info.get('id')
        if not thumb and vid:
            thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

        return {
            'id': info.get('id'),
            'url': url,
            'title': info.get('title', 'Unknown Title'),
            'duration': info.get('duration', 0),
            'thumbnail': thumb,
            'requester': requester,
            'stream_url': None # Будет получено непосредственно перед воспроизведением
        }

    async def resolve_stream_url(self, track: Dict) -> Optional[str]:
        """
        Получает прямую ссылку на аудиопоток.
        Должно вызываться асинхронно перед воспроизведением, чтобы ссылка не протухла.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._get_stream_url_sync, track['url'])
        except Exception as e:
            logger.error(f"Error resolving stream for {track['title']}: {e}")
            return None

    def _get_stream_url_sync(self, url: str) -> str:
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url'] # Прямая ссылка на ресурс
