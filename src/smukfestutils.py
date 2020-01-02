from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyClientCredentials
import argparse
import progressbar as pbar
import requests
import spotipy
import spotipy.util as util
import sys
import time
import urllib.request

def fromURLfindURI(spotify, name, url):
    user, urlType, refID = url.split('/')[-3:]

    if urlType == 'artist':
        result = spotify.artist(refID)
        nameURI = result['uri']
        return nameURI

    if urlType == 'playlist':
        result = spotify.user_playlist(user, refID)
        track = result['tracks']['items'][0]['track']
        nameURI = [artist['uri'] for artist in track['album']['artists']
                   if name in artist['name'].lower()][0]
        return nameURI

    if urlType == 'track':
        track = spotify.track(refID)
        nameURI = [artist['uri'] for artist in track['album']['artists']
                   if name in artist['name'].lower()][0]
        return nameURI

    return None


def artistURL():
    posterurl = 'https://www.smukfest.dk/musik/kunstnere-2020'
    response = requests.get(posterurl)

    soup = BeautifulSoup(response.text, "html.parser")

    a_tags = soup.findAll('a', {"class":"spots__link"})
    return ['https://www.smukfest.dk' + tag.attrs['href'] for tag in a_tags]

def URIsFromNames(spotify, uris, names):
    found = []
    artistURIs = uris.copy()
    missingNames = names.copy()
    for name, url in missingNames:
        print("Checking: ", name)
        print(url)
        result = findArtistURIFromNameOnly(spotify, name)
        if result is not None:
            artistURIs.append(result)
            found.append(name)
            print()

    for namefound in found:
        for name, url in missingNames[::-1]:
            if name == namefound:
                missingNames.remove((name, url))

    if len(missingNames) > 0:
        print(f"Still missing {len(missingNames)} artist URIs")
        print(missingNames)
    else:
        print("All artist URIs has been found!")
        dumpListToFile('artists.txt', artistURIs)

    return artistURIs, missingNames

def URIFromURL(spotify, spoturls):
    Pbar = pbar.ProgressBar()
    artistURIs = []
    for name, url in Pbar(spoturls):
        uri = fromURLfindURI(spotify, name, url)
        if uri is not None:
            artistURIs.append(uri)
    return artistURIs

def artistSpotifyURL(artisturls):
    spotifyurls = []
    missingNames = []
    Pbar = pbar.ProgressBar()
    for url in Pbar(artisturls):
        name = url.split('/')[-1].replace('-', ' ')
        spoturl = artist2spotifyURL(url)
        if spoturl is not None:
            spotifyurls.append((name.lower(), spoturl))
        else:
            missingNames.append((name, url))

    print(f"found {len(spotifyurls)} spotify-URLs out of {len(artisturls)} artists")
    return spotifyurls, missingNames

def artist2spotifyURL(artisturl):
    response = requests.get(artisturl)
    soup = BeautifulSoup(response.text, "html.parser")
    tags = soup.findAll('a', {"data-icon-before":"circle-spotify"})

    for elem in enumerate(tags):
        return elem[1]['href']
    return None


def dumpListToFile(fname, items):
    with open(fname, 'w+') as f:
        for item in items:
            f.write(item + '\n')


def findArtistURIFromNameOnly(spotify, name):
    result = spotify.search(q=name, type='artist')
    artists = result['artists']['items']
    artists = [item for item in artists if item['genres']]

    if len(artists) == 0:
        name = input("Please type the correct name: ")
        result = spotify.search(q=name, type='artist')
        artists = result['artists']['items']
        artists = [item for item in artists if item['genres']]

    if len(artists) == 0:
        return None
    if len(artists) == 1:
        return artists[0]['uri']

    print(f"Looking for artist: {name} - but found:")
    for j, item in enumerate(artists):
        print(f"[{j+1}]: {name}")
        for k, v in item.items():
            if k not in ['href', 'id']:
                print(f"{k:20}: {v}")
        print()

    while True:
        ans = int(input(f"Which artist is correct [1-{len(artists)}]? - [0] " +
                        "for none: ")) - 1
        if ans == -1:
            break
        if -1 < ans < len(artists):
            return result['artists']['items'][ans]['uri']
        print("Not a valid choice. Try again.")
    return None


def findArtistsTopN(spotifyClient, artistURI, n=5, v=False):
    trackURIS = []
    # Get artist name and id
    result = spotifyClient.artist(artistURI)
    name = result['name']
    sID = result['id']
    if v:
        print(name, sID)

    # find top tracks for artist
    result = spotifyClient.artist_top_tracks(sID)
    for track in result['tracks'][:n]:
        if v:
            print('track    : ' + track['name'] +'\nURI      :   '
                  + track['uri'])
        trackURIS.append(track['uri'])
    if v:
        print()
    return trackURIS

def loadArtistURI():
    with open("artistURI.txt") as f:
        output = [line.strip() for line in f]
    return output

def loadCridentials():
    with open("cridentials/ClientID") as f:
        cID = f.read().replace('\n', '')
    with open("cridentials/ClientSecret") as f:
        cSecret = f.read().replace('\n', '')
    return cID, cSecret

def setupSpotifyClient(username='jakob1379'):
    client_id, client_secret = loadCridentials()
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret)

    token = util.prompt_for_user_token(username,
                                       scope='playlist-modify-public',
                                       client_id=client_id,
                                       client_secret=client_secret,
                                       redirect_uri='https://localhost:8080')
    return spotipy.Spotify(
        client_credentials_manager=client_credentials_manager,
        auth=token)


def show_tracks(tracks):
    for i, item in enumerate(tracks['items']):
        track = item['track']
        print("   %d %32.32s %s" % (i, track['artists'][0]['name'],
                                    track['name']))

def listPlaylists(spotifyClient, username):
    playlists = spotifyClient.user_playlists(username)
    print()
    for playlist in playlists['items']:
        if playlist['owner']['id'] == username:
            print()
            print(playlist['name'], playlist['id'])
            print('  total tracks', playlist['tracks']['total'])


def tracksFromPlayList(spotifyClient, username, playlist): #
    results = spotifyClient.user_playlist(username, playlist_id=playlist)

    results = spotifyClient.user_playlist_tracks(username, playlist)
    tracks = results['items']
    while results['next']:
        results = spotifyClient.next(results)
        tracks.extend(results['items'])

    # print(temp_tracks['name'])
    return [track['track']['uri'] for track in tracks]


def loadTrackURIs(spotifyClient, uris=[], load=False, save=True):
    tracks = []
    if load:
        print("loading previous saved songs...")
        with open('data/tracks.txt') as f:
            for line in f:
                tracks.append(line.strip())
    else:
        print("finding artists top songs...")
        Pbar = pbar.ProgressBar()
        for uri in Pbar(uris):
            tracks += findArtistsTopN(spotifyClient, uri)

        if save:
            with open('tracks.txt', 'w+') as f:
                for track in tracks:
                    f.write(track + '\n')
    return tracks

def removeDuplicates(spotify, uris, user, playlist):
    Pbar = pbar.ProgressBar()
    tracks = [spotify.track(uri) for uri in Pbar(uris)]

    for k, v in tracks[0].items():
        if k not in ['album', 'available_markets', 'preview_url', 'explicit',
                     'disc_number']:
            print(f"{k+':':20}", v)


    for i, track in enumerate(tracks):

        otherTracks = tracks.copy()
        otherTracks.pop(i)

        for t in otherTracks:
            # check names
            if track['name'] in t['name']:
                # check artists
                otherArtists = [artist['name'] for artist in t['artists']]
                if any([artist['name'] in otherArtists
                        for artist in track['artists']]):
                    print()
                    print("duplicate name found for:")
                    print('[1] ', track['name'])
                    print("by ",
                          [artist['name'] for artist in track['artists']])
                    print("Matched by: ")
                    print('[2] ', t['name'])
                    print("by ",
                          [artist['name'] for artist in t['artists']])
                    print()
                    ans = int(
                        input("Which one [1/2] - 0 for none: ").strip()) - 1
                    if ans == -1:
                        pass
                    elif ans == 0:
                        spotify.user_playlist_remove_all_occurrences_of_tracks(
                            user, playlist, [track['id']])
                        tracks.remove(track)
                    elif ans == 1:
                        spotify.user_playlist_remove_all_occurrences_of_tracks(
                            user, playlist, [t['id']])
                        tracks.remove(t)

    uris = [track['uri'] for track in tracks]
    return uris
