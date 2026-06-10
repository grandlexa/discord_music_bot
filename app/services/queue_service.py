from typing import Dict, List, Optional
import random

class GuildQueue:
    def __init__(self):
        self.tracks: List[Dict] = []
        self.current_index: int = -1
        self.message = None # Discord message object for the player
        self.text_channel = None # Text channel to send player messages
        self.voice_client = None
        self.is_looping: bool = False
        
    def add_track(self, track: Dict):
        self.tracks.append(track)
        
    def clear(self):
        self.tracks = []
        self.current_index = -1
    
    def clear_future(self):
        """Очищает треки после текущего."""
        if self.current_index >= 0:
            self.tracks = self.tracks[:self.current_index + 1]
        else:
            self.tracks = []
    
    def clear_all_except_current(self):
        """Оставляет только текущий трек в очереди."""
        current = self.get_current_track()
        if current:
            self.tracks = [current]
            self.current_index = 0
        else:
            self.tracks = []
            self.current_index = -1
    
    def set_index(self, index: int):
        """Устанавливает текущий индекс без воспроизведения."""
        if 0 <= index < len(self.tracks):
            self.current_index = index
            return True
        return False
        
    def get_current_track(self) -> Optional[Dict]:
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None

    def get_next_track(self) -> Optional[Dict]:
        next_idx = self.current_index + 1
        if next_idx < len(self.tracks):
            self.current_index = next_idx
            return self.tracks[next_idx]
        return None
        
    def get_previous_track(self) -> Optional[Dict]:
        prev_idx = self.current_index - 1
        if prev_idx >= 0:
            self.current_index = prev_idx
            return self.tracks[prev_idx]
        return None

    def shuffle_remaining(self):
        """Перемешивает треки, которые еще не играли."""
        if self.current_index + 1 < len(self.tracks):
            remaining = self.tracks[self.current_index + 1:]
            random.shuffle(remaining)
            self.tracks = self.tracks[:self.current_index + 1] + remaining

    def get_queue_list(self) -> List[Dict]:
        """Возвращает список треков для отображения."""
        return self.tracks

class QueueService:
    def __init__(self):
        self._queues: Dict[int, GuildQueue] = {}

    def get_queue(self, guild_id: int) -> GuildQueue:
        if guild_id not in self._queues:
            self._queues[guild_id] = GuildQueue()
        return self._queues[guild_id]

    def remove_queue(self, guild_id: int):
        if guild_id in self._queues:
            del self._queues[guild_id]
