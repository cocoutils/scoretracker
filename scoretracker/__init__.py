from .scoretracker import ScoreTracker

async def setup(bot):
    """Red V3 setup function to load the cog."""
    await bot.add_cog(ScoreTracker(bot))
