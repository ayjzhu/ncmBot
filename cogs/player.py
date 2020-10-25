import discord
from discord.ext import commands
import asyncio
import math
# import queuelist
import os
from voiceState import VoiceState
from songQueue import SongQueue
from neteaseMusic import NeteaseMusic
import musicSource
import datetime
import time


class Player(commands.Cog, name = 'Music Playback Commands'):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.music = NeteaseMusic()
        self.currentSong = {}
        # self.playlist = queuelist.QueueList()
        # self.songs = SongQueue()
        self.voice_states = {}
    
    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.client, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.client.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        errorMsg = 'An error occurred: {}'.format(str(error))
        print(errorMsg)
        await ctx.send(errorMsg)


    @commands.Cog.listener()
    async def on_ready(self):
        print('Music playback commands are ready.')
    

    @commands.command(brief = 'Invite the bot to a voice channel.',
                        description = 'The bot will join a specified channel.\n'
                            'If no channel provided, the bot will join the author\'s channel instead.')
    async def join(self, ctx: commands.Context):
    # async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):

        # try:                        
        #     # default to author's channel
        #     if not channel:
        #         channel = ctx.author.voice.channel

        #     # move to a channel from a exist channel
        #     if ctx.voice_client:
        #         await ctx.voice.move_to(channel)
        #         return

        #     await channel.connect()

        # except Exception as e:
        #     print(f'ERROR: {type(e).__name__} - {e}')
        print('Current joined ', ctx.voice_state.voice)
        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()
        print('Current joined ', ctx.voice_state.voice)

    

    @commands.command(brief = 'Ask the bot to leave the voice channel.',
                        description = 'The bot will leave the current voice channel.')
    async def leave(self, ctx: commands.Context):
        # # check whether if there is a voice client connected
        # if ctx.voice_client:
        #     try:
        #         # stop any music before leaving
        #         if ctx.voice_client.is_playing():
        #             ctx.voice_client.stop()

        #         # # empty the playlist before leaving
        #         # if not self.playlist.isEmpty():
        #         #     self.playlist.clear()
        #     except Exception as e:
        #         print(f'**`ERROR:`** {type(e).__name__} - {e}')
        #     else:
        #         print(f'{self.client.user.name} has left the {ctx.voice_client.channel} channel.')
        #         await ctx.voice_client.disconnect()
        #         activity = discord.Activity(name = 'you', type = discord.ActivityType.listening)
        #         await self.client.change_presence(activity=activity)
        # else:
        #     await ctx.send('I\'m not even in a channel!')

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]


    @commands.command()
    async def search(self, ctx:commands.Context, *, keyword:str):
        # default displaying 10 results
        count = 10
        query = keyword.split('-')[-1]
        if query.isdigit() and 0 < int(query) < 50:
            count = int(query)

        author = ctx.author
        channel = ctx.channel
        menu = ''   # research results

        await ctx.trigger_typing()
        results = self.music.search(keyword)
        displayNum = results.get('query').get('numDisplayed')
        embed = discord.Embed(
            title = 'Search results of "%s":' % keyword,
            description = 'Please select a track from # 1-{}: '.format(displayNum),
            timestamp = datetime.datetime.utcnow(),
            colour = discord.Colour.green()
        ).set_footer(text = 'Current displays: %s/%s' % (displayNum, results.get('query').get('total')))

        for index, song in enumerate(results['info']):
            artist = ' & '.join([i['name'] for i in song['artist']])
            embed.add_field(
                name = '{} {}'.format(index+1, song['title']),
                value = '%s ~ %s • %s' % (artist, song['album']['name'], song['length']),
                inline = False
            )
            menu += '%02d: %s | %s | %s | %s' % (index+1, song['title'], artist, song['album']['name'], song['length']) + '\n'
        await ctx.send(embed = embed)
        # print(menu)

        # Automatically select if it has only one result
        if len(results['info']) == 1:
            return results['info'][0].get('id')

        # validate whether input is within bounds
        def is_valid(msg):
            selection = int(msg.content)
            return displayNum >= selection > 0

        try:    # getting user selection
            selection = await self.client.wait_for('message', check=is_valid, timeout=30)
        except asyncio.TimeoutError:
            await channel.send('Timeout! You took too long to decide..')
        else:   # post selection
            song = results['info'][int(selection.content)-1]
            # print(song)
            # await channel.send('ID for `{} - {}` is `{}`'.format(' & '.join([i['name'] for i in song['artist']]), song['title'], song.get('id')))
            return song.get('id')


    @commands.command()
    async def play(self, ctx:commands.Context, *, keyword:str):

        if not ctx.voice_state.voice:
            await ctx.invoke(self.join)
        songId = await ctx.invoke(self.search, keyword=keyword)

        await ctx.trigger_typing()
        try:
            source = await musicSource.NetEaseMusicSource.create_source(ctx, songId, br=320000, download=True)
        except musicSource.NetEaseMusicError as e:
            print(str(e))
            await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
        else:
            music = musicSource.Music(source)
            await ctx.voice_state.songs.put(music)
            # print(ctx.voice_state.songs)
            await ctx.send('Enqueued {}'.format(str(source)))
            # print('all voice states: ', self.voice_states)

            # await ctx.send(embed=song.create_embed())
            # ctx.voice_client.play(song.source, after=lambda e: print('Player error: %s' % e) if e else print('Finished playing!'))


    @commands.command()
    async def queue(self, ctx: commands.Context, *, page: int = 1):
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            artist = ' & '.join([i['name'] for i in song.source.data['artist']])
            queue += '`{0}.` {1} - [{2[title]}]({2[url]}) • {2[length]}\n'.format(i + 1, artist, song.source.data)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(ctx.voice_state.songs.size(), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)


    @commands.command()
    async def playlist(self, ctx:commands.Context, *, url:str):
        if not ctx.voice_state.voice:
            await ctx.invoke(self.join)
                    
        playlist = self.music.get_playlist(url)
        ids = playlist['playlist']['trackIds']

        # async with ctx.typing():
        await ctx.trigger_typing()
        message = await ctx.send('Enqueuing playlist...')
        for songId in ids:
            try:
                source = await musicSource.NetEaseMusicSource.create_source(ctx, songId, br=320000, download=False)
            except musicSource.NetEaseMusicError as e:
                print(str(e))
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                music = musicSource.Music(source)
                await ctx.voice_state.songs.put(music)
                await message.edit(content='Enqueued {}'.format(str(source)))
        await message.edit(content='All songs has been added to the player queue!')
        await message.add_reaction('\U0001F44D')


    @commands.command()
    async def lyric(self, ctx:commands.Context):
        if not ctx.voice_state.voice:
            await ctx.send('No song is playing currently!')
        else:
            currentSong = ctx.voice_state.current.source
            songId = currentSong.id
            try:
                lyric = self.music.get_lyric(songId)
            except Exception as e:
                print(f'ERROR: {type(e).__name__} - {e}')
                await ctx.send('Invalid `song ID` or `lyric` is unavaliable!')

            else:
                artist = ' & '.join([i['name'] for i in currentSong.data['artist']])            
                embed = (
                    discord.Embed(
                        title = '%s by %s' % (currentSong.data.get('title'), artist),
                        description = lyric.get('lyric') if lyric.get('lyric') else lyric['lrc'].get('lyric'),
                        color = discord.Color.orange()
                    )
                    .set_footer(text = 'Contributed by {0}'.format(
                        'N/A' if not lyric['contributor']['lyricUser'] else lyric['contributor']['lyricUser']['name'])
                    )
                )          
                await ctx.send(embed = embed)


    @commands.command()
    async def skip(self, ctx):
        # await ctx.invoke(self.stop)
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            activity = discord.Activity(name = 'you', type = discord.ActivityType.listening)
            await self.client.change_presence(activity=activity)
        else:
            await ctx.send('There is nothing playing!')        
        await ctx.send('Skipped!')
        # await ctx.invoke(self.background_player)


    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        else:
            await ctx.send('There is nothing playing!')


    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
        else:
            await ctx.send('Nothing to resume!')


    @commands.command()
    async def stop(self, ctx):
        # if ctx.voice_client.is_playing():
        #     ctx.voice_client.stop()
        #     activity = discord.Activity(name = 'you', type = discord.ActivityType.listening)
        #     await self.client.change_presence(activity=activity)
        # else:
        #     await ctx.send('There is nothing playing!')
        ctx.voice_state.songs.clear()
        print('playlist cleared!')
        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')
        


    @join.before_invoke
    @play.before_invoke
    @playlist.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        # if not ctx.author.voice or not ctx.author.voice.channel:
        #     await ctx.send("You are not connected to any voice channel.")
        #     raise commands.CommandError('Author is not connected to any voice channel.')

        # if ctx.voice_client is None:
        #     if ctx.author.voice:
        #         await ctx.author.voice.channel.connect()

        # # if ctx.voice_client:
        # #     if ctx.voice_client.channel != ctx.author.voice.channel:
        # #         raise commands.CommandError('Bot is already in a voice channel.')

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')


def setup(client):
    client.add_cog(Player(client))