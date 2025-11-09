from redbot.core import commands
import discord
import re
import unicodedata
from collections import defaultdict
import json
import os

SCORES_FILE = "scoretracker_scores.json"

class ScoreTracker(commands.Cog):
    """Tracks scores from a channel and maintains a leaderboard."""

    def __init__(self, bot):
        self.bot = bot
        self.source_channel_id = 1433148006508531773
        self.leaderboard_channel_id = 1362211269075276020
        self.scores = defaultdict(int)
        self.leaderboard_message_id = None

        # Load persisted scores if available
        self._load_scores()

    def _load_scores(self):
        if os.path.exists(SCORES_FILE):
            try:
                with open(SCORES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.scores = defaultdict(int, {k: int(v) for k, v in data.items()})
                print("[ScoreTracker] Loaded scores from JSON.")
            except Exception as e:
                print(f"[ScoreTracker] Failed to load scores: {e}")

    def _save_scores(self):
        try:
            with open(SCORES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=4)
            print("[ScoreTracker] Scores saved to JSON.")
        except Exception as e:
            print(f"[ScoreTracker] Failed to save scores: {e}")

    async def lbupdate(self):
        """Update or send the leaderboard embed."""
        channel = self.bot.get_channel(self.leaderboard_channel_id)
        if not channel:
            print("[ScoreTracker] Leaderboard channel not found.")
            return

        # Sort scores descending
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        description = "\n".join(f"**{user}**: {points} points" for user, points in sorted_scores)

        embed = discord.Embed(
            title="Swim Reapers Leaderboard",
            description=description or "No scores yet.",
            color=0x000000
        )

        # Edit existing or send new
        if self.leaderboard_message_id:
            try:
                msg = await channel.fetch_message(self.leaderboard_message_id)
                await msg.edit(embed=embed)
                return
            except discord.NotFound:
                self.leaderboard_message_id = None

        msg = await channel.send(embed=embed)
        self.leaderboard_message_id = msg.id
        print("[ScoreTracker] Leaderboard message sent/updated.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != self.source_channel_id:
            return

        normalized = unicodedata.normalize("NFKC", message.content)
        if "ѕсоrеd" not in normalized:
            print(f"[ScoreTracker] Message ignored (no 'ѕсоrеd'): {normalized}")
            return

        match = re.search(r"['\"]?(?P<user>.+?)['\"]?:?\s*ѕсоrеd\s*(?P<points>[\d,]+)", normalized)
        if not match:
            print(f"[ScoreTracker] Regex failed: {normalized}")
            return

        username = match.group("user").strip("'\"")
        points = int(match.group("points").replace(",", ""))

        # Keep only top score per user
        previous_score = self.scores.get(username, 0)
        if points > previous_score:
            self.scores[username] = points
            print(f"[ScoreTracker] {username} updated top score: {points}")
            self._save_scores()  # persist scores
            await self.lbupdate()
        else:
            print(f"[ScoreTracker] {username} score {points} ignored (top score {previous_score})")

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
            normalized = unicodedata.normalize("NFKC", message.content)
            if "ѕсоrеd" not in normalized:
                continue

            match = re.search(r"['\"]?(?P<user>.+?)['\"]?:?\s*ѕсоrеd\s*(?P<points>[\d,]+)", normalized)
            if match:
                username = match.group("user").strip("'\"")
                points = int(match.group("points").replace(",", ""))
                # Top score logic
                previous_score = self.scores.get(username, 0)
                if points > previous_score:
                    self.scores[username] = points
                    print(f"[ScoreTracker][Rebuild] {username} top score set to {points}")

        self._save_scores()
        await self.lbupdate()
        await ctx.send("Leaderboard rebuilt from channel history!")
