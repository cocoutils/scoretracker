from redbot.core import commands
import discord
import re
import unicodedata
from collections import defaultdict

class ScoreTracker(commands.Cog):
    """Tracks scores from a channel and maintains a leaderboard."""

    def __init__(self, bot):
        self.bot = bot
        self.source_channel_id = 1433148006508531773  # change to your source channel
        self.leaderboard_channel_id = 1362211269075276020  # change to your leaderboard channel
        self.scores = defaultdict(int)
        self.leaderboard_message_id = None  # stores the embed message ID

    async def lbupdate(self):
        """Update or send the leaderboard embed."""
        leaderboard_channel = self.bot.get_channel(self.leaderboard_channel_id)
        if not leaderboard_channel:
            print("Leaderboard channel not found.")
            return

        # Sort scores descending
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        description = "\n".join(f"**{user}**: {points} points" for user, points in sorted_scores)
        embed = discord.Embed(
            title="Swim Reapers Leaderboard",
            description=description or "No scores yet.",
            color=0x000000
        )

        # Edit existing message or send new
        if self.leaderboard_message_id:
            try:
                msg = await leaderboard_channel.fetch_message(self.leaderboard_message_id)
                await msg.edit(embed=embed)
                return
            except discord.NotFound:
                self.leaderboard_message_id = None  # message deleted

        # Send new leaderboard
        msg = await leaderboard_channel.send(embed=embed)
        self.leaderboard_message_id = msg.id

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore normal bots but allow webhooks
        if message.author.bot and not message.webhook_id:
            return

        if message.channel.id != self.source_channel_id:
            return

        normalized = unicodedata.normalize('NFKC', message.content)

        # Regex to match only webhook score messages (just ѕсоrеd + number)
        match = re.search(
            r"['\"]?(?P<user>.+?)['\"]?:\s*ѕсоrеd\s*(?P<points>[\d,]+)",
            normalized
        )

        if match:
            username = match.group('user').strip("'\"")  # remove surrounding quotes
            points = int(match.group('points').replace(',', ''))

            self.scores[username] += points
            print(f"Updated {username} with {points} points. Total: {self.scores[username]}")
            await self.lbupdate()

    @commands.command(name="lbrebuild")
    @commands.is_owner()
    async def lbrebuild(self, ctx):
        """Parse old messages and rebuild the leaderboard."""
        channel = self.bot.get_channel(self.source_channel_id)
        if not channel:
            await ctx.send("Source channel not found.")
            return

        self.scores.clear()
        async for message in channel.history(limit=None):
            # Ignore non-webhook bot messages
            if message.author.bot and not message.webhook_id:
                continue

            normalized = unicodedata.normalize('NFKC', message.content)
            match = re.search(
                r"['\"]?(?P<user>.+?)['\"]?:\s*ѕсоrеd\s*(?P<points>[\d,]+)",
                normalized
            )

            if match:
                username = match.group('user').strip("'\"")
                points = int(match.group('points').replace(',', ''))
                self.scores[username] += points

        await self.lbupdate()
        await ctx.send("Leaderboard rebuilt from channel history!")
