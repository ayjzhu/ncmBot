import requests
from configparser import ConfigParser
from pprint import pprint

class User():

    def __init__(self, uid:int=0):
        self.config = ConfigParser()
        self.config.read("config.ini", encoding="UTF-8")
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
            'Cookie': self.config.get('cred', 'cookie')
        }
        self.baseUrl = self.config.get('cred', 'ncmApi')

        self.userData = {
            'account' : dict(),
            'profile' : dict(),
            'playlists' : dict(
                count = 0,
            )
        }
        self.isLogIn = False
        self.cookie = None

    def login(self, email:str, pwd:str):
        params = {
            'email' : email,
            'password' : pwd
        }
        try:
            # get the current song info
            resp = requests.get(
                '{}login'.format(self.baseUrl),
                headers = self.headers,
                params = params
            ).json()

            # Login validation
            if resp['code'] != 200:
                raise ValueError('Incorrect! Please verify your password and try again.')
            else:
                print("Successfully logged in!")
                self.cookie = resp['cookie']
                self.isLogIn = True
                # Retrieve account infomation
                self.userData['account'].update(
                    userid = resp['account']['id'],
                    salt = resp['account']['salt'],
                    cookie = resp['cookie'],
                    isVip = True if resp['account']['vipType'] > 0 else False,
                    dateCreated = resp['account']['createTime']
                )

                # Retrieve personal profile infomation
                profile_data = {
                    'userid' : resp['profile']['userId'],
                    'userName' : resp['profile']['nickname'],
                    'signature' : resp['profile']['signature'],
                    'avatarPic' : {
                        'id' : resp['profile']['avatarImgId'],
                        'url' : resp['profile']['avatarUrl']
                    },
                    'backgroundPic' : {
                        'id' : resp['profile']['backgroundImgId'],
                        'url' : resp['profile']['backgroundUrl']
                    },
                    'birthday' : resp['profile']['birthday'],
                    'follows' : resp['profile']['followeds'],
                    'followers' : resp['profile']['follows'],
                    'profileUrl' : f"https://music.163.com/#/user?id={resp['profile']['userId']}" 
                }
                self.userData.update(profile = profile_data)

                # Retrieve playlists infomation
                self.userData['playlists'].update(count = resp['profile']['playlistCount'])
                self.userData['playlists'].update(subscribers = resp['profile']['playlistBeSubscribedCount'])
        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')

    def get_user(self):
        try:
            # get the current song info
            resp = requests.get(
                '{}login/status'.format(self.baseUrl),
                headers = self.headers
            ).json()

            if resp['code'] != 200:
                raise RuntimeError('You are not logged in!')
            else:
                self.userData['profile'] = resp['profile']

        except Exception as e:
            print(f'ERROR: {type(e).__name__} - {e}')


if __name__ == "__main__":
    u = User()
    u.login(email='', pwd='')
    pprint(u.userData)    