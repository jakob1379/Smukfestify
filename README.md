A program written in python to autogenerate a playlist in spotify with top tracks for the announced artists at Smukfest 20.

```
usage: smukfestify.py [-h] [-n [USER_NAME]] [-p [PLAYLIST]] [-l] [-r] [-a]

optional arguments:
  -h, --help            show this help message and exit
  -n [USER_NAME], --user-name [USER_NAME]
                        Provide your user name which can be optained by going
                        to https://open.spotify.com/ and vieweing your profile
  -p [PLAYLIST], --playlist [PLAYLIST]
                        id of the playlist to operate on
  -l, --list-playlists  if a user id is provided, list their playlists
  -r, --read-old-songs  Don't fetch songs anew, but read from last run
                        instead.
  -a, --read-artists    Don't fetch songs anew, but read from last run
                        instead.


```
