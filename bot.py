#https://discordapp.com/oauth2/authorize?client_id={CLIENTID}&scope=bot&permissions={PERMISSIONINT}
import os
import logging
import discord
import asyncio
from discord.ext import commands
from configparser import ConfigParser

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
config = ConfigParser()
config.read("config.ini", encoding="UTF-8")
client = commands.Bot(command_prefix = config.get("config", "prefix"))

def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog = f'cogs.{filename[:-3]}'
            client.load_extension(cog)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} - Discord version: {discord.__version__}')
    activity = discord.Activity(name = 'Music',
                                type = discord.ActivityType.listening)
    await client.change_presence(activity = activity)

def main():
    load_cogs()
    client.run(config.get("config", "token"))

if __name__ == "__main__":
    main()