import re
import requests
import datetime
from configparser import ConfigParser
from prettytable import PrettyTable

class QQMusic():
    '''
    A QQ music object that contains the essential attributes and methods of a song.
    '''

    def __init__(self):
        self.config = ConfigParser()
        self.config.read("config.ini", encoding="UTF-8")
        self.baseUrl = self.config.get('cred', 'qqmApi')
        self.cookie = self.config.get('cred', 'qqmCookie')
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
            'Cookie': self.cookie
        }
        self.musicMetadata = {
            'query' : dict(
                total = 0 ,
                pageNo = 0,
                pageSize = 0
            ),
            'info' : dict()
        }

    def setCookie(self):
        try:
            resp = requests.post(
                '{}user/setCookie'.format(self.baseUrl), 
                headers=self.headers,
                data={'data': self.cookie})
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            return resp


    def search(self, keywords:str, page=1, limit=20, _type=0):
        '''
        Search for music base on keywords. Precise search if `type` is specified.\n
        Types: 0 (default): song, 2: playlist, 7: lyric, 8: album, 9: artist, 12: mv

        :Args:
            - keywords `str`: search keyword
            - page `int`: starting page # from search results (default is 1)
            - limit `int`: limit for search results (default is 20)
            - _type `int` : type of search (deafult is 0 which for song)

        :Returns:
            - musicMetadata `dict`: metadata about the song (include title, artists, and album etc.)
        '''     
        params = {
            'key' : keywords,
            'pageNo': page,
            'pageSize': limit,
            't': _type
        }
        resp = requests.get(
            '{}search'.format(self.baseUrl),
            headers=self.headers,
            params=params
        ).json()
        songs = resp['data']['list']     # obtain data for songs  

        self.musicMetadata['query'].update(
            total = resp['data']['total'],
            pageNo = resp['data']['pageNo'],
            pageSize = resp['data']['pageSize']
        )

        results = list()
        convert = lambda t: datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')        
        for song in songs:
            sizes = {128: song['size128'], 320: song['size320'], 'flac': song['sizeflac']}
            result = {
                'title' : song['songname'],
                'songid' : song['songid'],
                'songmid' : song['songmid'],
                'artist' : [dict(name= artist['name'], id= artist['id'], mid= artist['mid']) for artist in song['singer']],
                'album' : {
                    'name' : song['albumname'],
                    'id' : song['albumid'],
                    'mid' : song['albummid'],
                    'publishTime' : convert(song['pubtime'])
                },
                'length': '%02d:%02d' %(divmod(song['interval'], 60)),                                  # convert ms to seconds
                'size': {size:'{:.1f} MB'.format(value/1_000_000) for size, value in sizes.items()},    # convert each bitrates to megabytes

            }
            result.update(songUrl= song.get('songurl', f'http://y.qq.com/#type=song&id={result["songid"]}')) # song url : https://y.qq.com/n/ryqq/songDetail/id
            results.append(result)
        self.musicMetadata.update(info=results)

        return self.musicMetadata


    def get_song(self, songmid:str, _type=320, isRedirect=0):
        params = {
            'id' : songmid,
            'type': _type,
            'isRedirect': isRedirect,
        }
        resp = requests.get(
            '{}song/url'.format(self.baseUrl),
            headers=self.headers,
            params=params
        ).json()
        return resp['data']


    def _get_playlist_id(self, url:str):
        '''
        Extract and return playlist id from an url
        '''
        try:
            resp = requests.get(
                url, 
                headers=self.headers)
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            playlist_id = re.findall(r'\Wid=(\d+)', resp.url)[0]
            return int(playlist_id)


    def get_playlist(self, _id:int):
        '''
        Retrieve all songs in a playlist
        '''
        resp = requests.get(
            '{}songlist'.format(self.baseUrl),
            headers=self.headers,
            params={'id' : _id}
        ).json()

        playlist = dict()
        data = resp['data']
        if data:
            convert = lambda t: datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')  
            playlist = {
                'name' : data['dissname'],
                'id' : int(data['disstid']),
                'creator' : data['nickname'],
                'createTime' : convert(data['ctime']),
                'description' : data['desc'],                           # empty if None
                'tags' : [tag.get('name') for tag in data['tags']],     
                'songCount' : data['songnum'],
                'playedCount' : data['visitnum'],
                'songids' : [int(i) for i in data['songids'].split(',')],
                'songmids' : [song['songmid'] for song in data['songlist']],
                'pic' : {
                    'logo' : data['logo'],
                    'profile' : data['headurl']
                }
            }
        return playlist


    def display(self):
        '''
        Display the formatted search result in a table
        
        :Args: 
         - Songs `dict`: result data cotaining query and info
        :Returns:
            None
        '''
        table = PrettyTable()
        table.field_names = ['#', 'Title', 'Artist', 'Album', 'Mid', 'Length']

        print('Total displayed: %s' % len(self.musicMetadata['info']))

        for index, song in enumerate(self.musicMetadata['info']) :
            names = ' & '.join([i['name'] for i in song['artist']])
            table.add_row([index+1, song['title'], names, song['album']['name'], song['songmid'], song['length']])
        table.align = 'l'

        # display to console
        # print(self.musicMetadata['info'])
        print(table)

        return table


if __name__ == "__main__":
    qq = QQMusic()
    # # testing search
    # keywords =  input("Search: ")
    # results = qq.search(keywords, limit = 10)
    # qq.display()   
    # selection = int(input('Select # of the song to download: '))
    # song = results['info'][selection-1]
    # print(song)
    # print(qq.get_song(song['songmid']))
    _id = qq._get_playlist_id('https://c.y.qq.com/base/fcgi-bin/u?__=fnd2C5sz4RmN')
    print(qq.get_playlist(_id))
                   