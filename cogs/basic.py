import discord
from configparser import ConfigParser
from discord.ext import commands

class Basic(commands.Cog, name = "Basic Commands"):

    def __init__(self, client):
        self.client = client
        self.config = ConfigParser()
        self.config.read("config.ini", encoding = "UTF-8")
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Basic commands are ready.")
    
    @commands.command(aliases = ['hello', 'sup', 'hi'], brief = 'Greets the user', description = 'The bot will greet the user.')
    async def greet(self, ctx):
        """A simple greeting to the user.
        """
        await ctx.send('Hello {}!'.format(ctx.author.name))

    @commands.command(brief='Display user\'s ping.', description='Shows the latency between the user and the server.')
    async def ping(self, ctx):
        await ctx.channel.send(f'{round(self.client.latency * 1000, 1)} ms')
    
    @commands.command(hidden = True)
    @commands.is_owner()
    async def logout(self, ctx):
        """[summary]
        Logout the bot
        Arguments:
            ctx {[string]} -- [context]
        """
        await ctx.send('Goodbye! Logging out...')
        print("Command sent by '%s', logging out..." % ctx.message.author)
        await self.client.logout()

def setup(client):
    client.add_cog(Basic(client))
