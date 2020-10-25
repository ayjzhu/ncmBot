import os
import discord
from discord.ext import commands
from neteaseMusic import NeteaseMusic


class NetEaseMusicError(Exception):
    pass


class NetEaseMusicSource(discord.PCMVolumeTransformer):
    
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, ctx:commands.Context, data:dict, source:discord.FFmpegPCMAudio, volume:float=0.75):
        super().__init__(source, volume)
        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data
        self.id = data.get('id')

    def __str__(self):
        return '**{0[filename]}** `ID:{0[id]}`'.format(self.data)

    @classmethod
    async def create_source(cls, ctx:commands.Context, songId:int, br=999000, download=False):
        ncm = NeteaseMusic()
        info = ncm.get_song(songId)[0]
        audioInfo = ncm.get_audio_file(info.get('id'), bitrate=br)
        print('Song info: ',info)

        if download:
            filename = 'songs/%s.%s' % (info['filename'], audioInfo['type'])
            # download the song if it does not exist
            if not os.path.exists(filename):
                ncm.download(songId, bitrate=320000)
            else:
                print('Looking up existing songs in library...')
            return cls(ctx, info, discord.FFmpegPCMAudio(filename))
        else:
            print('not downloading song')

        print('using url:', audioInfo['url'])
        return cls(ctx, info, discord.FFmpegPCMAudio(audioInfo['url'], **cls.FFMPEG_OPTIONS))


class Music:
    __slots__ = ('source', 'requester')

    def __init__(self, source: NetEaseMusicSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{} - {}\n```'.format(self.source.data.get('title'),
                               ' & '.join([i['name'] for i in self.source.data['artist']])),
                               color=discord.Color.blurple())
                 .add_field(name='Album', value= self.source.data['album']['name'])
                 .add_field(name='Duration', value=self.source.data.get('length'))
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Music Page', value='[Click]({})'.format(self.source.data.get('url')))
                 .add_field(name='ID', value=self.source.data.get('id'))
                 .set_thumbnail(url=self.source.data['album']['picture'])
                 .set_footer(text="Release on {}".format(self.source.data['album']['publishTime'])))

        return embed