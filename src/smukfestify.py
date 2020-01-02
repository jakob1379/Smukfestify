# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from smukfestutils import \
    artistURL, \
    artistSpotifyURL, \
    dumpListToFile, \
    findArtistURIFromNameOnly, \
    fromURLfindURI, \
    listPlaylists, \
    loadTrackURIs, \
    removeDuplicates, \
    setupSpotifyClient, \
    tracksFromPlayList, \
    URIsFromNames, \
    URIFromURL
import argparse
import progressbar as pbar
import sys

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--user-name",
                    help="Provide your user name which can be optained by " +
                    "going to https://open.spotify.com/ and vieweing" +
                    " your profile",
                    type=str,
                    nargs='?',
                    default='1130349271')
parser.add_argument("-p", "--playlist",
                    help="id of the playlist to operate on",
                    type=str,
                    nargs='?',
                    default='2zWYXDJT1rY2CVKQeCrzyI')
parser.add_argument("-l", "--list-playlists",
                    help="if a user id is provided, list their playlists",
                    action='store_true')
parser.add_argument("-r", "--read-old-songs",
                    help="Don't fetch songs anew, but read from last run instead.",
                    action='store_true')
parser.add_argument("-a", "--read-artists",
                    help="Don't fetch songs anew, but read from last run instead.",
                    action='store_true')


args = parser.parse_args()

USERID = args.user_name       #
PLAYLISTID = args.playlist


if __name__ == '__main__':
    print("Setting up spotify api parser...")
    sp = setupSpotifyClient(username=USERID)
    if args.list_playlists:
        listPlaylists(sp, USERID)
        sys.exit()

    if args.read_artists:
        print("Reading artist URIs...")
        with open('artists.txt') as f:
            artistURIs = [line.strip() for line in f]
    else:
        print("Extracting artist urls...")
        artisturls = artistURL()

        print("Searching for artist spotify urls...")
        spotifyurls, missingNames = artistSpotifyURL(artisturls)

        print("Extracting URIs from spotify URLs...")
        artistURIs = URIFromURL(sp, spotifyurls)

        print("Finding artist URI from names...")
        artistURIs, missingNames = URIsFromNames(sp, artistURIs, missingNames)

    print("Extract tracks from URI")
    tracksOnPlayList = tracksFromPlayList(sp, USERID, PLAYLISTID)
    tracks = loadTrackURIs(sp, artistURIs, load=args.read_old_songs)

    print(f"Removing duplicates...")
    tracks = removeDuplicates(sp, list(set(tracks+tracksOnPlayList)),
                              USERID, PLAYLISTID)

    # only add the tracks that are not already on the PLAYLIST
    print(f"Tracks found: {len(tracks)}")
    print(f"Tracks on playlist: {len(tracksOnPlayList)}")
    tracks = list(set(tracks) - set(tracksOnPlayList))

    if len(tracks) == 0:
        print("No new tracks to add.")
        sys.exit()

    print(f"Tracks with ids not on playlist: {len(tracks)}")
    ans = input("Should the missing tracks be added? [y/N] ")

    if ans.lower() == 'y':
        print("adding songs to playlist...")
        Bar = pbar.ProgressBar()
        for track in Bar(tracks):
            sp.user_playlist_add_tracks(USERID,
                                        playlist_id=PLAYLISTID,
                                        tracks=[track])
