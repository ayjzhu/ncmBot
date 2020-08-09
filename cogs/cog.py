import discord
from discord.ext import commands

class Cog(commands.Cog, name = "Cog Loads Commands"):

    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog commands are ready.')

    @commands.command(name = 'load', hidden = True)
    @commands.is_owner()
    async def load_cog(self, ctx, extension):
        cog = f'cogs.{extension}'
        self.client.load_extension(cog)
        print(f'{cog} has been loaded.')
        await ctx.send(f'`{extension} commands has been loaded.`')

    @commands.command(name = 'unload', hidden = True)
    @commands.is_owner()
    async def unload_cog(self, ctx, extension):
        cog = f'cogs.{extension}'
        try:
            self.client.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            print(f'{cog} has been unloaded.')
            await ctx.send(f'`{extension} commands has been unloaded.`')

    @commands.command(name = 'reload', hidden = True)
    @commands.is_owner()
    async def reload_cog(self, ctx, extension):
        cog = f'cogs.{extension}'
        self.client.reload_extension(cog)
        print(f'{cog} has been reloaded.')
        await ctx.send(f'`{extension} commands has been reloaded.`')

def setup(client):
    client.add_cog(Cog(client))
