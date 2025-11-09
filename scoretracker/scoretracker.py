from redbot.core import commands
import discord
import re
import unicodedata
from collections import defaultdict

class ScoreTracker(commands.Cog):
    """Tracks scores from a channel and maintains a leaderboard."""

    def __init__(self, bot):
        self.bot = bot
        self.source_channel_id = 1433148006508531773
        self.leaderboard_channel_id = 1362211269075276020
        self.scores = defaultdict(int)
        self.leaderboard_message_id = None

    async def update_leaderboard(self):
        leaderboard_channel = self.bot.get_channel(self.leaderboard_channel_id)
        if not leaderboard_channel:
            return

        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        description = "\n".join(f"**{user}**: {points} points" for user, points in sorted_scores)
        embed = discord.Embed(
            title="🏆 Leaderboard 🏆",
            description=description or "No scores yet.",
            color=discord.Color.gold()
        )

        if self.leaderboard_message_id:
            try:
                msg = await leaderboard_channel.fetch_message(self.leaderboard_message_id)
                await msg.edit(embed=embed)
                return
            except discord.NotFound:
                self.leaderboard_message_id = None

        msg = await leaderboard_channel.send(embed=embed)
        self.leaderboard_message_id = msg.id

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot and not message.webhook_id:
            return
        if message.channel.id != self.source_channel_id:
            return

        normalized = unicodedata.normalize('NFKC', message.content)
        match = re.match(r"(?P<user>.+?):\s*ѕсоrеd\s*(?P<points>[\d,]+)
        if match:
            username = match.group('user')
            points = int(match.group('points'))
            self.scores[username] += points
            await self.update_leaderboard()
