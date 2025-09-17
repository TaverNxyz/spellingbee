from .spellingbee import SpellingBee

async def setup(bot):
    await bot.add_cog(SpellingBee(bot))
