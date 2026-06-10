import discord
from discord.ui import View, Button, Modal, TextInput
from app.services.media_service import MediaService
from discord.ui import Select

class SeekModal(Modal, title="Перемотка трека"):
    time_input = TextInput(
        label="Время (мм:сс или секунды)",
        placeholder="например 1:30 или 90",
        required=True,
        max_length=10
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.cog.seek_track(interaction, self.time_input.value)

class PlayerEmbed:
    @staticmethod
    def create_playing_embed(track: dict, status: str = "Playing", volume: int = 100) -> discord.Embed:
        embed = discord.Embed(
            description=f"[{track['title']}]({track['url']})",
            color=discord.Color.green()
        )
        embed.set_author(name="🎵 Сейчас играет")
        if track.get('thumbnail'):
            embed.set_image(url=track['thumbnail'])
        
        duration = MediaService.parse_duration(track['duration'])
        embed.add_field(name="Длительность", value=duration, inline=True)
        embed.add_field(name="Заказал", value=track['requester'], inline=True)
        embed.add_field(name="Громкость", value=f"{volume}%", inline=True)
        
        return embed
    
    @staticmethod
    def create_queue_embed(tracks, current_index: int, page: int = 0, page_size: int = 15) -> discord.Embed:
        embed = discord.Embed(title="🎵 Очередь воспроизведения", color=discord.Color.blue())
        start = page * page_size
        end = min(start + page_size, len(tracks))
        desc = ""
        for i in range(start, end):
            track = tracks[i]
            prefix = "▶️ " if i == current_index else ""
            dur = MediaService.parse_duration(track.get('duration'))
            desc += f"{prefix}`{i+1}.` [{track.get('title','Unknown')}]({track.get('url')}) | {dur}\n"
        embed.description = desc or "❌ Очередь пуста."
        embed.set_footer(text=f"Стр. {page+1}/{(len(tracks)-1)//page_size + 1}")
        return embed

class PlayerView(View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    # Row 1
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def previous(self, interaction: discord.Interaction, button: Button):
        await self.cog.previous_track(interaction)

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.secondary, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: Button):
        await self.cog.toggle_pause(interaction)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.secondary, row=0)
    async def stop(self, interaction: discord.Interaction, button: Button):
        await self.cog.stop_player(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip(self, interaction: discord.Interaction, button: Button):
        await self.cog.skip_track(interaction)

    @discord.ui.button(label="Seek", emoji="⏩", style=discord.ButtonStyle.secondary, row=0)
    async def seek(self, interaction: discord.Interaction, button: Button):
        # Modal требует прямого ответа, не defer
        await interaction.response.send_modal(SeekModal(self.cog))

    # Row 2
    @discord.ui.button(label="Info", emoji="ℹ️", style=discord.ButtonStyle.secondary, row=1)
    async def info(self, interaction: discord.Interaction, button: Button):
        await self.cog.show_current_info(interaction)

    @discord.ui.button(label="List", emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    async def queue_list(self, interaction: discord.Interaction, button: Button):
        await self.cog.show_queue(interaction)

    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(self, interaction: discord.Interaction, button: Button):
        await self.cog.shuffle_queue(interaction)

    @discord.ui.button(label="Clear", emoji="🗑️", style=discord.ButtonStyle.secondary, row=1)
    async def clear(self, interaction: discord.Interaction, button: Button):
        await self.cog.clear_queue(interaction)

class QueueSelect(Select):
    def __init__(self, cog, guild_id, tracks, start_index: int, page_size: int):
        options = []
        subset = tracks[start_index:start_index+page_size]
        for idx, track in enumerate(subset):
            label = f"{start_index + idx + 1}. {track.get('title', 'Unknown')[:80]}"
            options.append(discord.SelectOption(label=label, value=str(start_index + idx)))
        super().__init__(placeholder="Выберите трек для воспроизведения", min_values=1, max_values=1, options=options)
        self.cog = cog
        self.guild_id = guild_id
    
    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        await self.cog.play_at_index(interaction, index)

class QueueView(View):
    def __init__(self, cog, guild_id, tracks, current_index: int, page: int = 0, page_size: int = 15):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.tracks = tracks
        self.current_index = current_index
        self.page = page
        self.page_size = page_size
        self.add_item(QueueSelect(cog, guild_id, tracks, page * page_size, page_size))
    
    @discord.ui.button(label="Prev", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: Button):
        if self.page > 0:
            self.page -= 1
        view = QueueView(self.cog, self.guild_id, self.tracks, self.current_index, self.page, self.page_size)
        embed = PlayerEmbed.create_queue_embed(self.tracks, self.current_index, self.page, self.page_size)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: Button):
        max_page = (len(self.tracks) - 1) // self.page_size
        if self.page < max_page:
            self.page += 1
        view = QueueView(self.cog, self.guild_id, self.tracks, self.current_index, self.page, self.page_size)
        embed = PlayerEmbed.create_queue_embed(self.tracks, self.current_index, self.page, self.page_size)
        await interaction.response.edit_message(embed=embed, view=view)
