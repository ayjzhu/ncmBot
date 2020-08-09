import os
import requests
import datetime
from prettytable import PrettyTable
from pprint import pprint

class NeteaseMusic():
    '''
    A music object that contains the essential attributes and methods of a song.
    '''

    def __init__(self):
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}
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
        resp = requests.get('{}search'.format(self.baseUrl),
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
                    # 'albumPic': song['album']['picUrl'],
                    'publishTime': convert(song['album']['publishTime']/1000),                                   # convert ms to seconds
                    'picid' : 18651015743755216
                },
                'length': '%02d:%02d' %(divmod(song['duration']/1000, 60)),                                    # convert ms to seconds
                'songid': song['id'],
                # 'size': {size:'{:.1f} MB'.format(value/1_000_000) for size, value in sizes.items()},    # convert each bitrates to megabytes
                'songurl': 'https://music.163.com/#/song?id=%s' % song['id']
            }
        
            results.append(result)

        self.musicData.update(info = results)
        # pprint(self.musicData)

        return self.musicData

    def getDownloadLink(self, id:int, bitrate = 999000):
        params = {
            'id' : id,
            'br' : bitrate
        }
        resp = requests.get('{}song/url'.format(self.baseUrl),
                                headers = self.headers,
                                params = params
        ).json()

        pprint(resp)

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

if __name__ == "__main__":
    nm = NeteaseMusic()
    # result = nm.search('minute', limit = 10)
    # nm.display()
    nm.getDownloadLink(123)