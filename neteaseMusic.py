import os
import requests
import datetime
from prettytable import PrettyTable
from pprint import pprint
from configparser import ConfigParser

class NeteaseMusic():
    '''
    A music object that contains the essential attributes and methods of a song.
    '''

    def __init__(self):
        self.config = ConfigParser()
        self.config.read("config.ini", encoding="UTF-8")
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
            'Cookie': self.config.get('cred', 'cookie')
        }
        self.baseUrl = 'https://ncm-api.herokuapp.com/'
        self.musicData = {
            'query' : dict(
                total = 0 ,
                numDisplayed = 0
            ),
            'info' : dict()
        }


    #1: 单曲, 10: 专辑, 100: 歌手, 1000: 歌单, 1002: 用户, 1004: MV, 1006: 歌词, 1009: 电台, 1014: 视频, 1018:综合
    def search(self, keywords:str, limit=10, offset=0, type=0):
        params = {
            'keywords' : keywords,
            'limit' : limit,
            'offset' : offset,
            'type' : 1,
        }
        resp = requests.get(
            '{}search'.format(self.baseUrl),
            headers=self.headers,
            params=params
        ).json()

        # obtain data for songs
        songs = resp['result']['songs']

        self.musicData['query'].update(
            total = resp['result']['songCount'],
            numDisplayed = len(songs)
        )

        results = []
        convert = lambda t: datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        for song in songs:
            result = {
                'title': song['name'],
                'artist': [dict(name= artist['name'], id= artist['id']) for artist in song['artists']],
                'album': {
                    'name': song['album']['name'],
                    'id': song['album']['id'],
                    'publishTime': convert(song['album']['publishTime']/1000),                                   # convert ms to seconds
                    'picid' : 18651015743755216
                },
                'length': '%02d:%02d' %(divmod(song['duration']/1000, 60)),                                    # convert ms to seconds
                'songid': song['id'],
                'songurl': 'https://music.163.com/#/song?id=%s' % song['id']
            }

            # the filename contains all of the artist names
            names = ' & '.join([i['name'] for i in result['artist']])
            filename = '%s - %s' % (names, result['title'])
            result.update(filename=filename)                # save the audio file name

            results.append(result)       # save each song info to a list
        # save the list the song info to the dictionary
        self.musicData.update(info = results)

        return self.musicData


    def search_by_id(self, id:int, bitrate=999000):
        params = {
            'id' : id,
            'br' : bitrate
        }

        try:
            # get the current song info
            resp = requests.get(
                '{}song/url'.format(self.baseUrl),
                headers = self.headers,
                params = params,
            ).json()

            pprint(resp)

            # validate status code
            if resp['code'] != 200 or resp['data'][0]['code'] != 200:
                raise ValueError('Invalid! Please double check your song ID.')
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            song = resp['data'][0]
            songData = {
                'id' : id,
                'url' : song['url'],
                'bitrate' : int(song['br'] / 1000),
                'size' : '%.1f MB' % (song['size']/1_000_000),   # convert each bitrates to megabytes
                'type' : song['type'],
                'quality' : song['level'],
                'fee' : 'vip only' if song['fee'] == 1 else 'free'
            }
            return songData


    def download(self, song:dict, bitrate=320000):

        # get the detail info of the song
        songInfo = self.search_by_id(song['songid'], bitrate=bitrate)
        try:
            # get the binary data from the download link
            data = requests.get(songInfo['url'], headers = self.headers).content

            # create a new directory if haven't done so
            fileDir = 'songs/'
            if not os.path.exists(fileDir):
                os.mkdir(fileDir)

            with open('%s%s.%s' % (fileDir, song['filename'], songInfo['type']), 'wb') as f:
                f.write(data)
                print("{}.{} {} download completed!".format(song['filename'], songInfo['type'], song['length']))
            return song['filename']
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')


    def display(self):
        '''
        Display the formatted search result in a table
        :Args: 
         - Songs `dict`: result data cotaining query and info
        :Returns:
            None
        '''
        table = PrettyTable()
        table.field_names = ['#', 'Title', 'Artist', 'Album', 'Length']

        print('Total displayed: %s' % len(self.musicData['info']))

        for index, song in enumerate(self.musicData['info']) :
            names = ' & '.join([i['name'] for i in song['artist']])
            table.add_row([index+1, song['title'], names, song['album']['name'], song['length']])
        table.align = 'l'

        # display to console
        print(table)

        return table

    def login(self):
        resp = requests.get(
            '{}login/status'.format(self.baseUrl),
            headers = self.headers
        )
        print(resp.status_code)

if __name__ == "__main__":
    nm = NeteaseMusic()

    ## testing search
    result = nm.search('minute', limit = 10)
    # nm.display()
    song = result['info'][1]
    pprint(song)

    ## testing download 1450574147  21224431  318143 1308010773
    # pprint(nm.search_by_id(2990399))
    nm.download(song, bitrate=990000)

    ## testing login functions
    # nm.login()

