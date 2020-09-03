import os
import re
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
        self.baseUrl = self.config.get('cred', 'ncmApi')
        self.musicMetadata = {
            'query' : dict(
                total = 0 ,
                numDisplayed = 0
            ),
            'info' : dict()
        }


    def search(self, keywords:str, limit=10, offset=0, type=1):
        '''
        Search for music base on keywords. Precise search if 'type' is supplied\n
        Types: 1: 单曲, 10: 专辑, 100: 歌手, 1000: 歌单, 1002: 用户, 1004: MV, 1006: 歌词, 1009: 电台, 1014: 视频, 1018:综合

        :Args:
            - keywords `str`: search keyword
            - limit `int`: limit for search results (default is 10)
            - offset `int`: offset from the search results (default is 0)
            - type `int` : type of search (deafult is 1 which for song)
        :Returns:
            - musicMetadata `dict`: metadata about the song (include artists, album, and length etc.)
        '''
        params = {
            'keywords' : keywords,
            'limit' : limit,
            'offset' : offset,
            'type' : type
        }
        resp = requests.get(
            '{}search'.format(self.baseUrl),
            headers=self.headers,
            params=params
        ).json()
        songs = resp['result']['songs']     # obtain data for songs

        self.musicMetadata['query'].update(
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
                    'picid' : song['album']['picId']
                },
                'length': '%02d:%02d' %(divmod(song['duration']/1000, 60)),                                    # convert ms to seconds
                'songId': song['id'],
                'songUrl': 'https://music.163.com/#/song?id=%s' % song['id']
            }

            # the filename contains all of the artist names
            names = ' & '.join([i['name'] for i in result['artist']])
            filename = '%s - %s' % (names, result['title'])
            result.update(filename=filename)                # save the audio file name

            results.append(result)       # save each song info to a list
        # save the list the song info to the dictionary
        self.musicMetadata.update(info = results)

        return self.musicMetadata


    def search_by_url(self, url:str):
        '''
        Search the metadata of the song given by its url or id

        :Args: 
            - url `str`: a NetEast music url which contains the song id 
        :Returns:
            - musicMetadata `dict`: metadata about the song (include artists, album, and length etc.)
        '''
        id = url
        # parse the song id from the url link
        if not url.isdigit():
            id = re.findall(r'\Wid=(\d+)', url)[0]
        musicMetadata = self.search(id)['info'][0]

        return musicMetadata


    def get_song_data(self, id:int, bitrate=999000):
        '''
        Retrieve the metadata of the song file (id, url, bitrate, size, type, quality, and fee)

        :Args: 
            - id `int`: song id of the song
        :Returns:
            - songData `dict`: detail data of the song file
        '''
        params = {
            'id' : id,
            'br' : bitrate
        }

        try:
            # get the current song info
            resp = requests.get(
                '{}song/url'.format(self.baseUrl),
                headers = self.headers,
                params = params
            ).json()

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
    

    def get_song_detail(self, *args):
        '''
        Get the detail infomation of the song

        :Args:
            - args `int`: song IDs
        :Returns:
            - results `dict`: metadata about the song (include artists, album, and length etc.)
        '''
        if len(args) > 1:
            # concatenate to a string with comma seperation
            ids = ','.join(map(str,args))
        else:
            ids = args

        try:
            resp = requests.get(
                '{}song/detail'.format(self.baseUrl),
                headers = self.headers,
                params = {
                    'ids' : ids
                }
            )
            songs = resp.json()['songs']
            # validate song id by checking if the list is empty
            if '"code":400' in resp.text or "Internal Server Error" in resp.text or not songs:
                raise ValueError('Invalid! Please double check your song ID.')
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            results = []
            for i in range(len(songs)):
                song = songs[i]
                privilege = resp.json()['privileges'][i]

                sizes = {
                    128000: song['l']['size'],
                    192000: song['m']['size'],
                    320000: song['h']['size']
                }
                    
                result = {
                    'title': song['name'],
                    'artist': [dict(name= artist['name'], id= artist['id']) for artist in song['ar']],
                    'album': {
                        'name': song['al']['name'],
                        'id': song['al']['id'],
                        'picture': song['al']['picUrl'],
                        'publishTime': self.timeConvert(song['publishTime']/1000)
                    },
                    'length': '%02d:%02d' %(divmod(song['dt']/1000,60)),                                    # convert ms to seconds
                    'songId': song['id'],
                    'size': {size:'{:.1f} MB'.format(value/1_000_000) for size, value in sizes.items()},    # convert each bitrates to megabytes
                    'fee' : '',
                    'maxBitrate' : privilege['maxbr'],
                    'songurl': 'https://music.163.com/#/song?id=%s' % song['id']
                }

                # update fee infomation
                if privilege['fee'] == 1:
                    result.update(fee='Vip Only')
                elif privilege['fee'] > 1:
                    result.update(fee='low bitrate free')
                else:
                    result.update(fee='free')

                # the filename contains all of the artist names
                names = ' & '.join([i['name'] for i in result['artist']])
                filename = '%s - %s' % (names, result['title'])
                # save the audio file name
                result.update(filename=filename)

                # save each song info to a list
                results.append(result)
            return results


    def get_playlist_detail(self):
        pass


    def get_playlist_songs(self, url:str):
        pass


    def download(self, songID:int, bitrate=999000):
        song = self.get_song_detail(songID)[0]
        # get the detail info of the song
        songData = self.get_song_data(song['songId'], bitrate=bitrate)
        try:
            print("{}.{} is downloading...".format(song['filename'], songData['type']))
            # get the binary data from the download link
            data = requests.get(songData['url'], headers = self.headers).content

            # create a new directory if haven't done so
            fileDir = 'songs/'
            if not os.path.exists(fileDir):
                os.mkdir(fileDir)

            with open('%s%s.%s' % (fileDir, song['filename'], songData['type']), 'wb') as f:
                f.write(data)
            print("{}.{} {} download completed!".format(song['filename'], songData['type'], songData['size']))

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

        print('Total displayed: %s' % len(self.musicMetadata['info']))

        for index, song in enumerate(self.musicMetadata['info']) :
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


    def timeConvert(self, timestamps:int):
        return datetime.datetime.fromtimestamp(timestamps/1000).strftime('%Y-%m-%d %H:%M:%S')


if __name__ == "__main__":
    nm = NeteaseMusic()

    # # testing search
    # keywords =  input("Search: ")
    # results = nm.search(keywords, type= 1, limit = 10)
    # nm.display()
    # selection = int(input('Select # of the song to download: '))
    # song = results['info'][selection-1]
    # pprint(song)
    # nm.download(song)

    ## testing download 1450574147  21224431  318143 1308010773
    # pprint(nm.get_song_data(2990399))

    # # testing login functions
    # nm.login()

    # # testing search by url
    # data = nm.search_by_url("http://music.163.com/song?id=26470629")
    # print(type(data))
    # pprint(data)

    # # testing playlist
    # # r = nm.get_song_detail(190508,251669,318143)
    # r = nm.get_song_detail(28909067)
    # for i in r:
    #     pprint(i)

    # r = nm.get_song_data(28909067,320000)
    # pprint(r)

    nm.download(28909067)
