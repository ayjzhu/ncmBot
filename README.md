# NetEase Cloud Music Bot
A Discord music bot that plays music on demand via NetEase Cloud Music

## Key Features
- Listen and share music together in a group
- Login and connect with personal NetEase Music account
    - Retrieve user information
    - Fetch user's playlists and import it to the playing queue
    - Modify/add songs to personal playlists
- View popular comments of a song
- Toggle lyric for current playing song
- Interative voting with `Like` or `Dislike` a song:
  - Liking a song will be add it to user's personal favorite playlist within the current Discord server
  - When a playing song gets a certain number of downvotes, it will be automatically __skipped__!
- Various ways of searching music:
    - By song names
    - By song ID or url
    - By playlist name or url
- Provide download to songs

## Development Roadmap
- Basic playback functionalities of a music player
    - [x] Load or import playlist to queue
    - [x] Play songs from a queue
    - [x] Song downloading
    - [x] Stop player and properly clear queue
- Admin
    - [x] Load or unload a category of commands while the bot is running
- Search engine
  - [x] Song/artist name
  - [x] Song url
  - [ ] Playlist url
  - [x] Precise type searching
  - [ ] Keyword recommendations
- Unique features
    - [x] User login
    - [x] Display popular comments
    - [x] Display lyric
    - [x] Fetch user infomation
    - [x] Fetch user's playlists
    - [ ] Interative voting of current song

## API In-Use
- Netease Cloud Music
- Discord Py

## Supported Source
- Netease Music
- QQ Music (WIP)
- YouTube Music (upcoming)

## Usages/Commands
The following commands start with a `.` symbol.
<br>*(ex. .play)*
___

### Playback
|Command|Function|
|---|---|
|play|Play the music|
|skip|Skip the current song|
|pause|Pause the music|
|stop|Stop the music|
|...|...|

### Cog*
|Command|Function|
|---|---|
|load|Load the extension file|
|unload|Load the extension file|
|reload|reload the extension file|

### known bugs
- `playlist` will stop enqueuing if invalid request from one of the song
- More efficient playlist enqueue
    - Enqueue song metainfo instead of the audio object
