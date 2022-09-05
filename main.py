import os
import discord
import motor.motor_asyncio
from discord.ext import commands

DISCORD_TOKEN = ""
MONGODB_URI = ""

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents = intents)

class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents = intents
        )

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                await bot.load_extension(f'cogs.{filename[:-3]}')

bot = MyBot()
bot.mongoConnect = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
bot.run (DISCORD_TOKEN)

