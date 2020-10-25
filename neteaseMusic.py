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


    def search(self, keywords:str, limit=10, offset=0, _type=1):
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
            'type' : _type
        }
        resp = requests.get(
            '{}search'.format(self.baseUrl),
            headers=self.headers,
            params=params
        ).json()
        songs = resp['result']['songs']     # obtain data for songs

        self.musicMetadata['query'].update(
            total = resp['result']['songCount'] if resp['result']['songCount'] > 0 else len(songs),
            numDisplayed = len(songs)
        )

        results = []
        convert = lambda t: datetime.datetime.fromtimestamp(t/1000).strftime('%Y-%m-%d %H:%M:%S')
        for song in songs:
            result = {
                'title': song['name'],
                'artist': [dict(name= artist['name'], id= artist['id']) for artist in song['artists']],
                'album': {
                    'name': song['album']['name'],
                    'id': song['album']['id'],
                    'publishTime': convert(song['album']['publishTime']),         # convert ms to seconds
                    'picid' : song['album']['picId']
                },
                'length': '%02d:%02d' %(divmod(song['duration']/1000, 60)),       # convert ms to seconds
                'id': song['id'],
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
                or `int`": the song id
        :Returns:
            - MusicMetaData `dict`: metadata about the song (include artists, album, and length etc.)
        '''
        id = url
        # parse the song id from the url link
        if not isinstance(id, int):
            id = re.findall(r'\Wid=(\d+)', url)[0]
        try:
            musicMetaData = self.get_song(id)

            if musicMetaData is None:
                raise ValueError('Invalid! Please double check your url link or song ID.')
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:                
            return musicMetaData[0]


    def get_audio_file(self, id:int, bitrate=999000):
        '''
        Retrieve the metadata of the song file (id, url, bitrate, size, type, quality, and fee)

        :Args: 
            - id `int`: song id of the song
        :Returns:
            - metaData `dict`: detail data of the song file
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
            metaData = {
                'id' : id,
                'url' : song['url'],
                'bitrate' : int(song['br'] / 1000),
                'size' : '%.1f MB' % (song['size']/1_000_000),   # convert each bitrates to megabytes
                'type' : song['type'],
                'quality' : song['level'],
                'fee' : 'vip only' if song['fee'] == 1 else 'free'
            }
            return metaData
    

    def get_song(self, ids):
        '''
        Get the detail infomation of the given song

        :Args:
            - ids `int`: song IDs
        :Returns:
            - results `list`: metadata about the song(s) (include artists, album, and length etc.)
        '''
        # concatenate to a string with comma seperation if it is a list
        if isinstance(ids, list):
            ids = ','.join(map(str,ids))

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

                # some songs may not have all available bitrates data
                sizes = {
                    128000: song.get('l').get('size') if song.get('l') is not None else 0,
                    192000: song.get('m').get('size') if song.get('m') is not None else 0,
                    320000: song.get('h').get('size') if song.get('h') is not None else 0
                }
                    
                result = {
                    'title': song['name'],
                    'artist': [dict(name= artist['name'], id= artist['id']) for artist in song['ar']],
                    'album': {
                        'name': song['al']['name'],
                        'id': song['al']['id'],
                        'picture': song['al']['picUrl'],
                        'publishTime': self.timeConvert(song['publishTime']) if song['publishTime'] > 0 else "N/A"
                    },
                    'length': '%02d:%02d' %(divmod(song['dt']/1000,60)),                                    # convert ms to seconds
                    'id': song['id'],
                    'size': {size:'{:.1f} MB'.format(value/1_000_000) for size, value in sizes.items()},    # convert each bitrates to megabytes
                    'fee' : '',
                    'maxBitrate' : privilege['maxbr'],
                    'url': 'https://music.163.com/#/song?id=%s' % song['id']
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


    def get_playlist(self, url:str):
        '''
        Get the detail infomation of the given playlist

        :Args:
            - url `str`: a NetEast music playlist url which contains the playlist id
                or `int`": the song id
        :Returns:
            - result `dict`: metadata about the playlist (include a list of trackIds, playlist, and creator info etc.)
        '''

        pid = url
        # parse the playlist id from the url link
        if not isinstance(pid, int):
            pid = re.findall(r'\Wid=(\d+)', url)[0]
        try:
            resp = requests.get(
                '{}playlist/detail'.format(self.baseUrl),
                headers = self.headers,
                params = {
                    'id' : pid
                }
            ).json()
            # validate playlist id
            if resp['code'] != 200:
                raise ValueError('Invalid! Please double check your playlist ID.')
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            playlist = resp['playlist']
            result = {
                'playlist' : {
                    'name' : playlist['name'],
                    'id' : playlist['id'],
                    'description' : playlist['description'],
                    'count' : {
                        'play' : playlist['playCount'],
                        'track' : playlist['trackCount']
                    },
                    'tag' : playlist['tags'],
                    'coverImage' : playlist['coverImgUrl'],
                    'date' : {
                        'create' : self.timeConvert(playlist['createTime']),
                        'update' : self.timeConvert(playlist['trackUpdateTime']), # changes when playlist order or new song updates
                        'add' : self.timeConvert(playlist['trackNumberUpdateTime'])   # changes only when new song update
                    },
                    'follower' : playlist['subscribedCount'],
                    'trackIds' : []
                },
                'creator' : {
                    'userName' : playlist['creator']['nickname'],
                    'userId' : playlist['creator']['userId'],
                    'signature' : playlist['creator']['signature'],
                    'picture': {
                        'avatar' : {
                            'id' : playlist['creator']['avatarImgId'],
                            'url' : playlist['creator']['avatarUrl']
                        },
                        'background' : {
                            'id' : playlist['creator']['backgroundImgId'],
                            'url' : playlist['creator']['backgroundUrl']
                        }
                    },
                    'birthday' : self.timeConvert(playlist['creator']['birthday']),
                    'isVip' : True if playlist['creator']['vipType'] > 0 else False,
                    'url' : f"https://music.163.com/#/user?id={playlist['creator']['userId']}" 
                }
            }

            # add tracks id in the playlist
            for track in playlist['trackIds']:
                result['playlist']['trackIds'].append(track['id'])
            
            return result


    def get_lyric(self, id:int):
        # assuing the given song has lyric
        try:
            resp = requests.get(
                '{}lyric'.format(self.baseUrl),
                headers = self.headers,
                params = {
                    'id' : id
                }
            ).json()
            
            # validate song id
            if resp.get('nolyric'):
                raise TypeError('Pure Music! No lyric is avalible.')
            elif not 'lrc' in resp or resp['code'] != 200:
                raise ValueError('Invalid song ID or lyric is unavaliable!')
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            result = {
                'id' : None if not resp.get('lyricUser') else resp['lyricUser'].get('id'), # song id
                'contributor' : {
                    'lyricUser' : None if not resp.get('lyricUser') else {
                        'name' : resp['lyricUser']['nickname'],
                        'id' : resp['lyricUser']['userid'],
                        'publishTime' : self.timeConvert(resp['lyricUser']['uptime'])                        
                    }
                },
                'lrc' : {
                    'version' : resp['lrc']['version'],
                    'lyric' : re.sub(r'\[(.+?)\]', '', resp['lrc']['lyric']) # remove the timestamps
                    # 'lyric' : resp['lrc']['lyric']
                },
                'transLrc' : {      # not all songs have translation
                    'version' : resp['tlyric'].get('version'),
                     # remove the timestamps
                    'lyric' : re.sub(r'\[(.+?)\]', '', resp['tlyric']['lyric']) if resp['tlyric'].get('lyric') else None
                    # 'lyric' : resp['tlyric'].get('lyric')
                }
            }

            # check if there is infomation of the translating user
            if resp.get('transUser'):
                result['contributor'].update({
                    'transUser' :{
                        'name' : resp['transUser']['nickname'],
                        'id' : resp['transUser']['userid'],
                        'publishTime' : self.timeConvert(resp['transUser']['uptime'])
                    }
                })

            # combining the original and translated lyric if exists
            if result['transLrc'].get('lyric'):
                # convert the lyric from string to list and remove all '\n'
                lyricList = list(filter(None, result['lrc']['lyric'].splitlines()))
                transLrcList = list(filter(None, result['transLrc']['lyric'].splitlines()))

                # combined both lyric list element-wise and join them to a 
                diff = len(lyricList) - len(transLrcList)     # offset the union list by the difference length in each list
                if diff == 0:
                    combinedLyricList = [i + '\n' + j for i, j in zip(lyricList, transLrcList)]
                elif diff > 0:
                    combinedLyricList = lyricList[:diff] + [i + '\n' + j for i, j in zip(lyricList[diff:], transLrcList)]
                else:
                    combinedLyricList = transLrcList[:diff] + [i + '\n' + j for i, j in zip(lyricList, transLrcList[diff:])]

                combinedLyricStr = '\n'.join(combinedLyricList)
                result.update(lyric= combinedLyricStr)

            return result


    # private method to fetch comment
    def __get_comments(self, comments:list):
        '''
        Fetch the comments and store into a list

        :Args:
            - comment `list`: a list contains the comments
        :Returns:
            - result `list`: a list of comments with user info
        '''        
        if comments is None:
            return None
        
        results = []
        for hc in comments:
            comment = {
                'user' : {
                    'name' : hc['user']['nickname'],
                    'id' : hc['user']['userId'],
                    'avatar' : hc['user']['avatarUrl'],
                    'isVip' : True if hc['user']['vipType'] > 0 else False
                },
                'comment' : {
                    'id' : hc['commentId'],
                    'content' : hc['content'],
                    'time' : self.timeConvert(hc['time']),
                    'likes' : hc['likedCount'],
                    'isLiked' : hc['liked'],
                },
            }
            # add the parent comment if it exist
            if hc['beReplied']:
                parentComment = hc['beReplied'][0]
                comment.update({
                    'parentComment' : {
                        'user' : {
                            'name' : parentComment['user']['nickname'],
                            'id' : parentComment['user']['userId'],
                            'avatar' : parentComment['user']['avatarUrl'],
                            'isVip' : True if parentComment['user']['vipType'] > 0 else False
                        },
                        'comment' : {
                            'id' : parentComment['beRepliedCommentId'],
                            'content' : parentComment['content']
                        }                         
                    }
                })
            results.append(comment)
        return results


    def get_hot_comments(self, id:int, _type=0, limit=20, offset=0):
        # 0:song, 1:mv, 2:playlist, 3:album, 4:radio, 5:video

        params = {
            'id' : id,
            'limit' : limit,
            'offset' : offset,
            'type' : _type
        }
        try:
            resp = requests.get(
                '{}comment/hot'.format(self.baseUrl),
                headers=self.headers,
                params=params
            ).json()

            if resp['code'] != 200:
                raise ValueError('Invalid! Please double check your song ID.')
            elif resp['total'] == 0:   # invalid id or no comment
                return None
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            results = dict(
                hotComments = self.__get_comments(resp['hotComments']),
                total = resp['total'],
                more = resp['hasMore']
            )
            return results


    def get_music_comments(self, id:int, limit=20, offset=0, isHotComment=True):
        params = {
            'id' : id,
            'limit' : limit,
            'offset' : offset
        }
        try:
            resp = requests.get(
                '{}comment/music'.format(self.baseUrl),
                headers=self.headers,
                params=params
            ).json()

            if resp['code'] != 200:
                raise ValueError('Invalid! Please double check your song ID.')
            elif resp['total'] == 0:   # invalid id or no comment
                return None
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            results = dict(
                comments = self.__get_comments(resp['comments']),
                total = resp['total'],
                more = resp['more']
            )
            if isHotComment:
                results.update(hotComments = self.__get_comments(resp['hotComments']))
            return results


    def set_like_to_comment(self, id:int, cid:int, toLike=True, _type=0):
        params = {
            'id' : id,
            'cid' : cid,
            't' : 1 if toLike else 0,
            'type' : _type
        }
        try:
            resp = requests.get(
                '{}comment/like'.format(self.baseUrl),
                headers=self.headers,
                params=params
            ).json()
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
        else:
            return "Sucess!" if resp['code'] == 200 else 'Fail!'


    def download(self, id:int, bitrate=999000):
        # get the detail info of the song
        song = self.get_song(id)[0]
        print("Music infomation of {} is obtained!".format(song['filename']))

        # get the info of the music file
        fileData = self.get_audio_file(song['id'], bitrate=bitrate)
        try:
            filename = '{}.{}'.format(song['filename'], fileData['type'])
            print("{} is downloading...".format(filename))
            # get the binary data from the download link
            data = requests.get(fileData['url'], headers = self.headers).content

            # create a new directory if haven't done so
            fileDir = 'songs/'
            if not os.path.exists(fileDir):
                os.mkdir(fileDir)

            with open('%s%s' % (fileDir, filename), 'wb') as f:
                f.write(data)
            print("{} in {} download completed!".format(filename, fileData['size']))

            return filename
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
    # results = nm.search(keywords, _type= 1, limit = 10)
    # nm.display()
    # selection = int(input('Select # of the song to download: '))
    # song = results['info'][selection-1]
    # pprint(song)
    # nm.download(song)

    ## testing download 1450574147  21224431  318143 1308010773
    # pprint(nm.get_audio_file(2990399))

    # testing login functions
    # nm.login()

    # # testing search by url
    # data = nm.search_by_url('https://music.163.com/#/song?id=96391')
    # pprint(data)

    # # testing get song details
    # # r = nm.get_song(190508,251669,318143)
    # r = nm.get_song(28909067)
    # for i in r:
    #     pprint(i)

    # r = nm.get_audio_file(28909067,320000)
    # pprint(r)

    ## testing get playlist
    # playlist = nm.get_playlist(2683935608)
    # playlist = nm.get_playlist('http://music.163.com/playlist?id=4869945748&userid=315274012')
    # print((playlist['playlist']['trackIds']))
    # pprint(nm.get_song(playlist['playlist']['trackIds']))

    # testing get lyric
    # 524148119, 1405281921 318143
    ly = nm.get_lyric(3986241)
    pprint(ly)


    # testing get comments 3203846 501846756 263648
    # c = nm.get_hot_comments(501846756, limit=10)
    # c = nm.get_music_comments(501846756, limit=5)
    # pprint(c)

    # testing like a comment
    # 1485705313
    # print(nm.set_like_to_comment(501846756,cid=3443989791, toLike=False))
    

    # print(nm.download(191783))
