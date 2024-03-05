import discord
import asyncio
from discord.ext import commands
import os
import sys
import yaml

with open('./config.yml', 'r') as file:
    data = yaml.load(file, Loader=yaml.CLoader)

if data["token"] is None:
    token = os.environ.get('token')
else:
    token = data["token"]

if token is None:
    sys.exit("Bot token is not specified neither in config file nor environment.")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", strip_after_prefix=True, case_insensitive=True, intents=intents)

async def loadcogs(folder):
    for cog in os.listdir(f"./cogs/{folder}"):
        if cog.endswith(".py"):
            try:
                cog = f"cogs.{folder}.{cog.replace('.py','')}"
                await bot.load_extension(cog)
            except Exception as e:
                print(f"{cog} cannot be loaded")
                raise e

async def main():
    async with bot:
        await loadcogs("Events")
        print("Events Loaded!")

        await loadcogs("Info")
        print("Info Loaded!")

        await loadcogs("Utility")
        print("Utility Loaded!")

        await bot.start(token)

asyncio.run(main())