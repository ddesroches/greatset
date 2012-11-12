"""
Great Set!

Input parameters:
 - duration (minutes)
 - venue (club, wedding, dinner)
 """

import json
import sys
import random
import subprocess
import os

from pyechonest import config, song, track

club_map = [
           ( 0, {'energy': (0.5, 0.8), 'danceability': (0.6, 1.0), 'tempo': (100, 120)}),
           (30, {'energy': (0.1, 0.4), 'danceability': (0.0, 0.6), 'tempo': ( 60, 100)}),
           (35, {'energy': (0.5, 0.8), 'danceability': (0.6, 1.0), 'tempo': (100, 120)}),
           (70, {'energy': (0.1, 0.4), 'danceability': (0.0, 0.6), 'tempo': ( 60, 100)}),
           (75, {'energy': (0.7, 1.0), 'danceability': (0.8, 1.0), 'tempo': (120, 200)})
           ]
wedding_map = [
           ( 0, {'energy': (0.4, 0.6), 'danceability': (0.6, 1.0), 'tempo': (100, 120)}),
           (15, {'energy': (0.1, 0.4), 'danceability': (0.0, 0.6), 'tempo': ( 60,  90)}),
           ( 0, {'energy': (0.5, 0.8), 'danceability': (0.6, 1.0), 'tempo': (100, 120)}),
           (35, {'energy': (0.1, 0.4), 'danceability': (0.0, 0.6), 'tempo': ( 60,  90)}),
           (60, {'energy': (0.5, 0.8), 'danceability': (0.6, 1.0), 'tempo': (100, 120)}),
           (75, {'energy': (0.1, 0.4), 'danceability': (0.0, 0.6), 'tempo': ( 60,  90)}),
           (95, {'energy': (0.6, 0.9), 'danceability': (0.8, 1.0), 'tempo': (110, 180)})
             ]
dinner_map = [
           ( 0, {'energy': (0.0, 0.3), 'danceability': (0.0, 0.4), 'tempo': ( 50, 90)})
             ]
SET_MAPS = {'club': {'priority': 'danceability', 'map': club_map},
            'wedding': {'priority': 'tempo', 'map': wedding_map},
            'dinner': {'priority': 'energy', 'map': dinner_map}
           }

MAPS = {'club': club_map, 'dinner': dinner_map, 'wedding': wedding_map}

def get_set_types():
    return SET_MAPS.keys()
    
def get_best_audio_track(song_id, catalog, pysong=None):
    """
    Get the best (audio) track for a given song in the given catalog.
    Returns a dict with {'track': ..., 'duration': ..., etc.}
    """
    if not pysong:
        pysong = song.Song(song_id)
    tracks = pysong.get_tracks(catalog)
    best_track = None
    for t in tracks:
        pytrack = track.track_from_id(t['id'])
        if pytrack.__dict__.get('tempo'):
            # track has audio features
            best_track = pytrack
            foreign_id = t['foreign_id']
            break
            
    if best_track:
        result = {'track': best_track.id,
                  'title': best_track.title,
                  'duration': best_track.duration,
                  'tempo': pysong.audio_summary['tempo'],
                  'energy': pysong.audio_summary['energy'],
                  'danceability': pysong.audio_summary['danceability'],
                  'loudness': best_track.loudness,
                  'foreign_id': foreign_id.split(':')[2],
                  'hotttnesss': pysong.song_hotttnesss,
                  'familiarity': pysong.artist_familiarity,
                  'song': pysong.id
                 }
        return result
    else:
        return None

def init_track_db(pysongs):
    track_db = []
    for s in pysongs:
        result = get_best_audio_track(s.id, 'spotify-WW', pysong=s)
        if result:
            track_db.append(result)
        else:
            print "No audio tracks found for %s." % s.id
    return track_db

def init_track_db_for_artist(artist_name):
    pysongs = song.search(artist=artist_name, buckets=['tracks','id:spotify-WW'], results=100)
    return init_track_db(pysongs)

#TRACK_DB = init_track_db_for_artist("Squarepusher")
TRACK_DB = json.load(open('song_db.json'))

def get_all_tracks():
    return TRACK_DB

def add_track_to_db(tr):
    TRACK_DB.append(tr)
    f = open('song_db.json', 'w')
    json.dump(TRACK_DB, f)
    f.close()
    
def _in_range(val, minmax):
    return val >= minmax[0] and val <= minmax[1]
    
def find_target_track(track_values, target_attr, priority):
    """
    Find a track among track_values that most closely matches the attributes.
    """
    energy_ok = set()
    danceability_ok = set()
    tempo_ok = set()
    for i,t in enumerate(track_values):
        if _in_range(t['energy'], target_attr['energy']):
            energy_ok.add(i)
        if _in_range(t['danceability'], target_attr['danceability']):
            danceability_ok.add(i)
        if _in_range(t['tempo'], target_attr['tempo']):
            tempo_ok.add(i)

    tracks = energy_ok.intersection(danceability_ok).intersection(tempo_ok)
    if len(tracks) > 0:
        return track_values[tracks.pop()]
    else:
        tracks = energy_ok.intersection(tempo_ok)
        if len(tracks) > 0:
            return track_values[tracks.pop()]
        else:
            if len(energy_ok):
                return track_values[energy_ok.pop()]
            elif len(track_values) > 0:
                # nothing found in range. fall back to first track.
                return track_values[0]
            else:
                # No more tracks!
                return None

def make_set(setLength, setType):
    """
    Makes a set of the given length and type.
    Returns a list of track dicts in sequence.
    """
    results = []
    track_values = TRACK_DB
    random.shuffle(track_values)
    set_duration = setLength * 60.0

    settype = setType.lower()
    set_map = SET_MAPS[settype]['map']
    set_priority = SET_MAPS[settype]['priority']

    total_duration = 0.0
    map_index = 0

    while map_index < len(set_map) and total_duration < set_duration and len(track_values) > 0:
        
        print("total_duration: %5.1f, set_duration: %5.1f" % (total_duration, set_duration))

        chunk_map = set_map[map_index]    
        # Make a chunk given a duration and target.
        if len(set_map) > map_index + 1:
            next_target = set_map[map_index+1]
        else:
            next_target = None # end of the set
        
        # chunk duration is in secs
        chunk_duration = set_duration * float((next_target[0] if next_target else 100) - chunk_map[0]) / 100.0
        chunk_so_far = 0.0
        
        print("Building a chunk of %5.1f" % chunk_duration)
        
        while chunk_so_far < (0.95 * chunk_duration):
            # Find songs that fit the target for the next duration range.
            # This always returns a track if one is available.
            tr = find_target_track(track_values, chunk_map[1], set_priority)
            if tr:
                results.append(tr)
                chunk_so_far += tr['duration']
                track_values.remove(tr)
            else:
                # No more tracks!
                break

        print("Built a chunk of %5.1f" % chunk_so_far)

        total_duration += chunk_so_far
        # Subtract any duration overage from the total set duration.
        # This helps prevent the total set from running over.
        if chunk_so_far > chunk_duration:
            set_duration -= (chunk_so_far - chunk_duration)
        map_index += 1
        
    return results

def play(play_tracks):
    track_list = ','.join([i['foreign_id'] for i in play_tracks])    
    cmd = "open spotify:trackset:GreatSet:%s" % track_list
    subprocess.call(cmd, shell=True)

if __name__ == "__main__":
    play()
