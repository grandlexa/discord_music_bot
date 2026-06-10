import discord
from discord.ext import commands
import asyncio
import logging

from app.services.queue_service import QueueService
from app.services.youtube_service import YouTubeService
from app.services.media_service import MediaService
from app.ui.player_view import PlayerView, PlayerEmbed

logger = logging.getLogger("music_cog")

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_service = QueueService()
        self.youtube_service = YouTubeService()

    async def _ensure_voice(self, ctx):
        if not ctx.author.voice:
            await ctx.send("❌ Вы должны быть в голосовом канале!")
            return False
        
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        return True

    @commands.command(name="play", aliases=["з", "p", "здфн"])
    async def play(self, ctx, *, query: str):
        if not await self._ensure_voice(ctx):
            return

        msg = await ctx.send(f"🔎 Поиск: **{query}**...")
        
        # Поиск треков (в executor)
        loop = self.bot.loop
        try:
            tracks = await loop.run_in_executor(
                None, 
                self.youtube_service.search_and_extract, 
                query, 
                ctx.author.mention
            )
        except Exception as e:
            await msg.edit(content=f"❌ Ошибка поиска: {str(e)}")
            return

        if not tracks:
            await msg.edit(content="❌ Ничего не найдено.")
            return

        queue = self.queue_service.get_queue(ctx.guild.id)
        queue.voice_client = ctx.voice_client
        queue.text_channel = ctx.channel

        for track in tracks:
            queue.add_track(track)

        if len(tracks) == 1:
            await msg.edit(content=f"✅ Добавлено в очередь: **{tracks[0]['title']}**")
        else:
            await msg.edit(content=f"✅ Добавлено {len(tracks)} треков в очередь.")

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.play_next(ctx.guild.id)

    async def play_next(self, guild_id):
        queue = self.queue_service.get_queue(guild_id)
        vc = queue.voice_client
        
        if not vc:
            return

        track = queue.get_next_track()
        if not track:
            # Очередь закончилась, запускаем таймер отключения
            self.bot.loop.create_task(self.auto_disconnect(guild_id))
            if queue.message:
                try:
                    await queue.message.delete()
                    queue.message = None
                except discord.HTTPException:
                    pass
            self.queue_service.remove_queue(guild_id)
            return

        # Разрешаем ссылку на поток
        stream_url = await self.youtube_service.resolve_stream_url(track)
        if not stream_url:
            await self.play_next(guild_id) # Skip bad track
            return

        # Создаем источник
        try:
            start_time = int(track.get('start_time', 0) or 0)
            source = MediaService.create_source(stream_url, start_time=start_time)
            
            # Fade-in эффект (запуск таска)
            if start_time == 0:
                source.volume = 0.0
            else:
                source.volume = vc.source.volume if vc.source else 1.0
            
            vc.play(source, after=lambda e: self.bot.loop.create_task(self.play_next_callback(guild_id, e)))
            
            if start_time == 0:
                self.bot.loop.create_task(MediaService.volume_fade(vc, 0.0, 1.0, duration=2.0))

            # Отправляем UI
            vol_percent = int(source.volume * 100)
            embed = PlayerEmbed.create_playing_embed(track, volume=vol_percent)
            view = PlayerView(self, guild_id)
            
            # Удаляем старое сообщение плеера если есть
            if queue.message:
                try:
                    await queue.message.delete()
                except discord.HTTPException:
                    pass
            
            if queue.text_channel:
                queue.message = await queue.text_channel.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Playback error: {e}")
            await self.play_next(guild_id)

    async def auto_disconnect(self, guild_id):
        """Таймер авто-отключения при простое."""
        await asyncio.sleep(120) # 2 минуты
        # Проверяем актуальность состояния
        # Если бот все еще подключен, не играет и очередь пуста
        queue = self.queue_service.get_queue(guild_id)
        vc = queue.voice_client
        
        # Если vc None, значит уже отключились
        if not vc or not vc.is_connected():
            return

        # Если играет музыка или очередь не пуста (и мы не в конце) - отмена
        if vc.is_playing() or (queue.current_index + 1 < len(queue.tracks)):
            return

        await vc.disconnect()

    async def play_next_callback(self, guild_id, error):
        if error:
            logger.error(f"Player error: {error}")
        await self.play_next(guild_id)

    # UI Interaction Handlers
    async def toggle_pause(self, interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("❌ Не подключен", ephemeral=True)
            return

        queue = self.queue_service.get_queue(interaction.guild_id)
        track = queue.get_current_track()
        
        if vc.is_playing():
            vc.pause()
            if track:
                vol = int(vc.source.volume * 100) if vc.source else 100
                embed = PlayerEmbed.create_playing_embed(track, status="⏸️ На паузе", volume=vol)
                await interaction.response.edit_message(embed=embed)
            else:
                await interaction.response.send_message("⏸️ Пауза", ephemeral=True)
                
        elif vc.is_paused():
            vc.resume()
            if track:
                vol = int(vc.source.volume * 100) if vc.source else 100
                embed = PlayerEmbed.create_playing_embed(track, status="🎵 Сейчас играет", volume=vol)
                await interaction.response.edit_message(embed=embed)
            else:
                await interaction.response.send_message("▶️ Продолжаем", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Не играет", ephemeral=True)

    async def skip_track(self, interaction):
        vc = interaction.guild.voice_client
        if vc:
            await interaction.response.defer()
            vc.stop() 
        else:
            await interaction.response.send_message("❌ Не играет", ephemeral=True)

    async def stop_player(self, interaction):
        queue = self.queue_service.get_queue(interaction.guild_id)
        queue.clear()
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await vc.disconnect()
        
        await interaction.response.edit_message(content="⏹️ Плеер остановлен", embed=None, view=None)

    async def previous_track(self, interaction):
        queue = self.queue_service.get_queue(interaction.guild_id)
        if queue.current_index > 0:
            queue.current_index -= 2
            vc = interaction.guild.voice_client
            if vc:
                await interaction.response.defer()
                vc.stop()
        else:
            await interaction.response.send_message("❌ Это первый трек", ephemeral=True)

    async def seek_track(self, interaction, time_str):
        # Парсинг времени
        seconds = 0
        try:
            parts = time_str.split(':')
            if len(parts) == 1:
                seconds = int(parts[0])
            elif len(parts) == 2:
                seconds = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                raise ValueError
            
            logger.info(f"Seeking to {seconds} seconds (input: {time_str})")
        except ValueError:
            await interaction.followup.send("❌ Неверный формат времени. Используйте секунды или ММ:СС", ephemeral=True)
            return

        queue = self.queue_service.get_queue(interaction.guild_id)
        track = queue.get_current_track()
        if not track:
            return

        # Устанавливаем start_time и перезапускаем
        track['start_time'] = seconds
        queue.current_index -= 1 # Чтобы play_next взял этот же трек
        
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            
        # Убираем сообщение о перемотке, так как SeekModal уже сделал defer, 
        # а сообщение плеера будет удалено и пересоздано.
        # Если мы не ответим на defer, состояние "Thinking..." может висеть.
        # Но сообщение, к которому привязан interaction (кнопка Seek), будет удалено.
        # Так что это безопасно.
        # await interaction.followup.send(f"⏩ Перемотка на {time_str}", ephemeral=True)

    async def play_at_index(self, interaction, index: int):
        """Переключение на выбранный трек из списка очереди."""
        queue = self.queue_service.get_queue(interaction.guild_id)
        if 0 <= index < len(queue.tracks):
            # выставляем индекс так, чтобы следующий play_next взял нужный трек
            queue.current_index = index - 1
            vc = interaction.guild.voice_client
            if vc:
                await interaction.response.defer()
                vc.stop()
        else:
            await interaction.response.send_message("❌ Неверный номер трека", ephemeral=True)

    async def show_current_info(self, interaction):
        queue = self.queue_service.get_queue(interaction.guild_id)
        track = queue.get_current_track()
        commands_info = (
            "**Команды и кнопки:**\n"
            "`!play <запрос>` — добавить трек/плейлист в очередь (алиасы: `!з`, `!p`, `!здфн`)\n Поддерживаются youtube ссылки на треки, плейлисты и поиск по названию.\n"
            "`!queue` — 📜List показать очередь\n"
            "`!shuffle` — 🔀Shuffle перемешать будущие треки\n"
            "`!volume <0-100>` — установить громкость\n"
            "ℹ️ Info - Вывод информации о текущем треке и краткая справка\n"
            "⏩ Seek — перемотка\n"
            "🗑️ Clear — очистить очередь"
            
        )
        if track:
            vc = interaction.guild.voice_client
            vol = int(vc.source.volume * 100) if vc and vc.source else 100
            embed = PlayerEmbed.create_playing_embed(track, volume=vol)
            embed.add_field(name="Справка", value=commands_info, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="ℹ️ Информация", description="❌ Ничего не играет", color=discord.Color.red())
            embed.add_field(name="Справка", value=commands_info, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def clear_queue(self, interaction):
        queue = self.queue_service.get_queue(interaction.guild_id)
        queue.clear_all_except_current()
        await interaction.response.send_message("🗑️ Очередь очищена, текущий трек сохранен", ephemeral=True)

    async def show_queue(self, interaction):
        queue = self.queue_service.get_queue(interaction.guild_id)
        tracks = queue.get_queue_list()
        
        if not tracks or (len(tracks) == 1 and queue.current_index == 0):
            await interaction.response.send_message("❌ Очередь пуста.", ephemeral=True)
            return
        
        from app.ui.player_view import PlayerEmbed, QueueView
        page = 0
        page_size = 15
        embed = PlayerEmbed.create_queue_embed(tracks, queue.current_index, page, page_size)
        view = QueueView(self, interaction.guild_id, tracks, queue.current_index, page, page_size)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def shuffle_queue(self, interaction):
        queue = self.queue_service.get_queue(interaction.guild_id)
        queue.shuffle_remaining()
        await interaction.response.send_message("🔀 Очередь перемешана", ephemeral=True)

    @commands.command(name="queue", aliases=["q", "list"])
    async def queue(self, ctx):
        queue = self.queue_service.get_queue(ctx.guild.id)
        tracks = queue.get_queue_list()
        
        if not tracks:
            await ctx.send("❌ Очередь пуста.")
            return

        embed = discord.Embed(title="🎵 Очередь воспроизведения", color=discord.Color.blue())
        
        desc = ""
        for i, track in enumerate(tracks):
            prefix = ""
            if i == queue.current_index:
                prefix = "▶️ "
            
            desc += f"{prefix}`{i+1}.` [{track['title']}]({track['url']}) | {MediaService.parse_duration(track['duration'])}\n"
            
            # Ограничение Discord на длину сообщения
            if len(desc) > 1900:
                desc += "... и другие"
                break
        
        embed.description = desc
        await ctx.send(embed=embed)

    @commands.command(name="shuffle")
    async def shuffle_command(self, ctx):
        queue = self.queue_service.get_queue(ctx.guild.id)
        queue.shuffle_remaining()
        await ctx.send("🔀 Очередь перемешана.")

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx, volume: int = None):
        if not ctx.voice_client:
            await ctx.send("❌ Я не подключен к голосовому каналу.")
            return
        
        if volume is None:
            vc = ctx.voice_client
            vol = int(vc.source.volume * 100) if vc and vc.source else 100
            await ctx.send(f"🔊 Текущая громкость: **{vol}%**\nИспользование: `!volume <0-100>`")
            return
        
        if not 0 <= volume <= 100:
            await ctx.send("❌ Громкость должна быть от 0 до 100.")
            return

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"🔊 Громкость установлена на **{volume}%**")

    @commands.command()
    async def stop(self, ctx):
        queue = self.queue_service.get_queue(ctx.guild.id)
        queue.clear()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Бот остановлен.")

async def setup(bot):
    await bot.add_cog(Music(bot))
