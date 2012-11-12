import json
import sys

from pyechonest import config, song

import setlist

def main(infile, outfile):
    song_ids = open(infile).read().split('\n')[:-1]

    results = []
    for s in song_ids:
        print(s), ":",
        result = setlist.get_best_audio_track(s, 'spotify-WW')
        if result:
            results.append(result)
            print(result)
        else:
            print "No audio tracks found."

    song_db = open(outfile, 'w')
    json.dump(results, song_db)
    song_db.close()

if __name__ == "__main__":
    sys.exit(main("song_ids.txt", "new_song_db.json"))
