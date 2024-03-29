import requests
from configparser import ConfigParser
from pprint import pprint
import datetime

class User():

    def __init__(self, uid:int=0):
        self.config = ConfigParser()
        self.config.read("config.ini", encoding="UTF-8")
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
            'Cookie': self.config.get('cred', 'cookie')
        }
        self.baseUrl = self.config.get('cred', 'ncmApi')

        self.isLogIn = False
        self.uid = uid
        self.userData = {
            'account' : dict(),     # obtain through login
            'profile' : dict(),
            'playlists' : dict(
                count = 0,
                subscribers = 0
            )
        }


    def timeConvert(self, timestamps:int):
        return datetime.datetime.fromtimestamp(timestamps/1000).strftime('%Y-%m-%d %H:%M:%S')


    def login(self, email:str, pwd:str):
        try:
            # get the current song info
            resp = requests.get(
                '{}login'.format(self.baseUrl),
                headers = self.headers,
                params = {
                            'email' : email,
                            'password' : pwd
                        }
            ).json()

            # Login validation
            if resp['code'] != 200:
                raise ValueError('Incorrect! Please verify your username or password and try again.')
            else:
                print("Successfully logged in!")
                self.isLogIn = True
                # Retrieve account infomation
                self.userData['account'].update(
                    userId = resp['account']['id'],
                    salt = resp['account']['salt'],
                    token = resp['token'],
                    cookie = resp['cookie']
                )
                return self.userData
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')


    def get_user(self, uid:int):
        try:
            # get the current song info
            resp = requests.get(
                '{}user/detail'.format(self.baseUrl),
                headers = self.headers,
                params= {
                    'uid' : uid
                }
            ).json()

            if resp['code'] != 200:
                raise ValueError('Invalid! Please double check your user ID.')
            else:
                # Retrieve personal profile infomation
                profile_data = {
                    'userId' : resp['profile']['userId'],
                    'userName' : resp['profile']['nickname'],
                    'signature' : resp['profile']['signature'],
                    'level' : resp['level'],
                    'listenSongs' : resp['listenSongs'],
                    'balance' : resp['userPoint']['balance'],
                    'updateTime' : self.timeConvert(resp['userPoint']['updateTime']),
                    'picture': {
                        'avatar' : {
                            'id' : resp['profile']['avatarImgId'],
                            'url' : resp['profile']['avatarUrl']
                        },
                        'background' : {
                            'id' : resp['profile']['backgroundImgId'],
                            'url' : resp['profile']['backgroundUrl']
                        }
                    },
                    'birthday' : resp['profile']['birthday'],
                    'follows' : resp['profile']['followeds'],
                    'followers' : resp['profile']['follows'],
                    'dateCreated' : self.timeConvert(resp['profile']['createTime']),
                    'daysCreated' : resp['createDays'],
                    'isVip' : True if resp['profile']['vipType'] > 0 else False,
                    'url' : f"https://music.163.com/#/user?id={resp['profile']['userId']}" 
                }
                self.userData.update(profile = profile_data)
                # Retrieve playlists infomation
                self.userData['playlists'].update(count = resp['profile']['playlistCount'])
                self.userData['playlists'].update(subscribers = resp['profile']['playlistBeSubscribedCount'])

                return self.userData
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')


    def is_login(self):
        resp = requests.get(
            '{}login/status'.format(self.baseUrl),
            headers = self.headers
        ).json()

        try:
            if resp['code'] != 200:
                raise RuntimeError('Invalid! You are not logged in.')
            else:
                return resp['profile']
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')

    
    def get_subcount(self):
        resp = requests.get(
            '{}user/subcount'.format(self.baseUrl),
            headers = self.headers
        ).json()

        try:
            if resp['code'] != 200:
                raise RuntimeError('Invalid! You are not logged in.')
            else:
                data = {
                    'mvCount' : resp['mvCount'],
                    'djRadioCount' : resp['djRadioCount'],
                    'createDjRadioCount' : resp['createDjRadioCount'],
                    'artistCount' : resp['artistCount'],
                    'createdPlaylistCount' : resp['createdPlaylistCount'],
                    'subPlaylistCount' : resp['subPlaylistCount']
                }
                return data
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')


    def logout(self):
        try:
            resp = requests.get(
                '{}logout'.format(self.baseUrl),
                headers = self.headers
            ).json()

            if resp['code'] != 200:
                raise RuntimeError('You are not logged in!')
            print("Successfully logged out!")
            return resp
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')
    

    def get_playlists(self, uid:int):
        try:
            resp = requests.get(
                '{}user/playlist'.format(self.baseUrl),
                headers = self.headers,
                params= {
                    'uid' : uid
                }
            ).json()

            if not resp['playlist']:
                raise ValueError('Invalid! Please double check your user ID or the user does not have any playlist')
            else:
                playlists = resp['playlist']
                data = {
                    'count' : len(playlists),
                    'playlists' : dict()
                }

                results = []
                for playlist in playlists:
                    result = {}
                    result.update(
                        # creator = self.get_user(uid),
                        name = playlist['name'],
                        id = playlist['id'],
                        description = playlist['description'],
                        count = {
                            'plays' : playlist['playCount'],
                            'tracks' : playlist['trackCount']
                        },
                        tags = playlist['tags'],
                        coverImage = playlist['coverImgUrl'],
                        date = {
                            'create' : self.timeConvert(playlist['createTime']),
                            'update' : self.timeConvert(playlist['trackUpdateTime']), # changes when playlist order or new song updates
                            'add' : self.timeConvert(playlist['trackNumberUpdateTime'])   # changes only when new song update
                        },
                        followers = playlist['subscribedCount'],
                        own = True if playlist['creator']['userId'] == uid else False
                    )
                    results.append(result)
                data.update(playlists = results)
                return data

        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')



if __name__ == "__main__":
    u = User()
    # print(u.is_login())
    # u.login(email='@126.com', pwd='')
    print(u.get_subcount())
    user_id = u.is_login()['userId']
    playlists = u.get_playlists(user_id)

    # for index, p in enumerate( playlists['playlists']) :
    #     print('{1}. {0}'.format(p['name'], index+1))

    count = 0
    for p in playlists['playlists']:
        if p['own'] == True:
            count += 1
    print(count)
    print(playlists['count'])

    # pprint(u.get_user(user_id))
