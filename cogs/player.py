import discord
import asyncio
import queuelist
import os
from neteaseMusic import NeteaseMusic
from discord.ext import commands
import datetime
import time

class Player(commands.Cog, name = 'Music Playback Commands'):
    def __init__(self, client):
        self.client = client
        self.music = NeteaseMusic()
        self.currentSong = {}
        self.playlist = queuelist.QueueList()


    @commands.Cog.listener()
    async def on_ready(self):
        print('Music playback commands are ready.')
    

    @commands.command(brief = 'Invite the bot to a voice channel.',
                        description = 'The bot will join a specified channel.\n'
                            'If no channel provided, the bot will join tha author\'s channel ')
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        try:
            if ctx.voice_client is not None:    # move the bot to other channel if its already in a channel
                await ctx.voice_client.move_to(channel)
                print('Voice client is occupided')
            else:
                print('Voice client is empty')
                channel = ctx.author.voice.channel
                await channel.connect()    # connect to a specific channel if the bot hasn't been to any channel

            print(f'{self.client.user.name} has joined the {channel} channel.')
        except Exception as e:
            if isinstance(e, AttributeError):
                await ctx.send(f'*{self.client.user.name} has already been in the channel!*')
            print(f'**`ERROR:`** {type(e).__name__} - {e}')


    @commands.command(brief = 'Ask the bot to leave the voice channel.',
                        description = 'The bot will leave the current voice channel.')
    async def leave(self, ctx: commands.Context):
        # check whether if there is a voice client connected
        if ctx.voice_client:
            try:
                # stop any music before leaving
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                # empty the playlist before leaving
                if not self.playlist.isEmpty():
                    self.playlist.clear()
            except Exception as e:
                print(f'**`ERROR:`** {type(e).__name__} - {e}')
            else:
                print(f'{self.client.user.name} has left the {ctx.voice_client.channel} channel.')
                await ctx.voice_client.disconnect()
                activity = discord.Activity(name = 'you | .help', type = discord.ActivityType.listening)
                await self.client.change_presence(activity=activity)
        else:
            await ctx.send('I\'m not even in a channel!')


def setup(client):
    client.add_cog(Player(client))