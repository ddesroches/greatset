import os
import operator
import cherrypy
from pyechonest import config, song

import setlist

HEAD = """
<doctype html>
<html>
<title>Great Set!</title>
<head>
<h1>Great Set!</h1>
<h3>by David & Nick DesRoches for <a href="http://boston.musichackday.org/2012">Music Hack Day Boston 2012</a></h3>
<a href = "http://the.echonest.com"><p><img src="/images/echo_nest_logo.gif" alt="Powered by The Echo Nest"></p></a>
</head>
<body>
BODY_HERE
</body>
</html>
"""

class GreatSet(object):
    def __init__(self):
        self.track_list = None

    def index(self):
        return HEAD.replace("BODY_HERE", open("body.html").read())
    index.exposed = True

    def playTracks(self):
        setlist.play(self.track_list)
    playTracks.exposed = True
    
    def make_set(self, setLength, setType):
        self.track_list = setlist.make_set(int(setLength), setType)

        body = self._make_track_table(self.track_list)
        #body = '<form action = "playTracks" method = "get"><input type = "submit" value = "Play in Spotify"></form>'
        spotify_ids = ','.join([t['foreign_id'] for t in self.track_list])
        body += '<p><p><b>Play this set in Spotify</b><br>'
        body += '<iframe src="https://embed.spotify.com/?uri=spotify:trackset:GREAT_SET:%s" frameborder="0" allowtransparency="true"></iframe>' % spotify_ids
        return HEAD.replace("BODY_HERE", body)
    make_set.exposed = True

    def add_song(self, artist, title):
        songs = song.search(artist=artist, title=title, results=5, sort="song_hotttnesss-desc")
        self.track_list = []
        for s in songs:
            tr = setlist.get_best_audio_track(s.id, "spotify-WW", pysong=s)
            if tr:
                self.track_list.append(tr)
        
        body = 'Which one of these tracks do you like?<br>'
        body += '<form action = "add_track" method = "get"><input type = "text" style="width:150" name = "track_id" placeholder = "Track ID"'
        body += '<input type = "submit"></form>'
        body += self._make_track_table(self.track_list)
        return HEAD.replace("BODY_HERE", body)
    add_song.exposed = True

    def add_track(self, track_id):
        for t in self.track_list:
            if track_id == t["track"]:
                setlist.add_track_to_db(t)
                break
        return self.index()
    add_track.exposed = True

    def make_full_set(self, sortBy):
        self.track_list = setlist.get_all_tracks()
        self.track_list.sort(key=operator.itemgetter(sortBy))
        
        body = '<form action = "add_song" method = "get"><input type = "text" name = "artist" style="width:150" placeholder = "artist name">'
        body += '<input type = "text" name = "title" style="width:150" placeholder = "song title">&nbsp;'
        body += '<input type = "submit" value = "Add Song"></form>'
        body += self._make_track_table(self.track_list)
        return HEAD.replace("BODY_HERE", body)
    make_full_set.exposed = True

    def _make_track_table(self, track_list):
        # Start the table
        table = '<table border="1"><tr><th>Spotify</th> <th>Hotttnesss</th> <th>Familiarity</th> <th>Duration</th> <th>Tempo</th> <th>Energy</th> <th>Danceability</th><th>Track ID</th> </tr>'
        totalDuration = 0
        for t in track_list:
            if t["hotttnesss"] > 0.65:
                hotttnessColor = "red"
            elif t["hotttnesss"] > 0.4:
                hotttnessColor = "orange"
            elif t["hotttnesss"] > 0.15:
                hotttnessColor = "yellow"
            else:
                hotttnessColor = "blue"

            familiarityColor = "white"

            if t["energy"] > 0.75:
                energyColor = "red"
            elif t["energy"] > 0.5:
                energyColor = "orange"
            elif t["energy"] > 0.25:
                energyColor = "yellow"
            else:
                energyColor = "blue"
                
            totalDuration += t["duration"]
            minutes = int(t["duration"] / 60)
            seconds = int(t["duration"] % 60)
            duration = "%d:%.2d" % (minutes, seconds)
            
            table += '<tr>'
            table += '<td><iframe src="https://embed.spotify.com/?uri=spotify:track:%s" frameborder="0" width="400" height="80" allowtransparency="true"></iframe></td>' % t["foreign_id"]
            table += '<td align="center" bgcolor=' + hotttnessColor + '>%1.3f</td>' % t["hotttnesss"]
            table += '<td align="center" bgcolor=' + familiarityColor + '>%1.3f</td>' % t["familiarity"]
            table += '<td align="center">' + duration + '</td>'
            table += '<td align="center">%3.1f BPM</td>' % t['tempo']
            table += '<td align="center" bgcolor=' + energyColor + '>%1.3f</td>' % t["energy"]
            table += '<td align="center">%1.3f</td>' % t["danceability"]
            table += '<td align="center">' + t["track"] + '</td>'
            table += '</tr>'
            
        minutes = int(totalDuration / 60)
        seconds = int(totalDuration % 60)
        totalDuration = "%d:%.2d" % (minutes, seconds)
        table += '<tr><th align="right">Total Duration</td> <th align="center">' + totalDuration + '</td> </tr></table>'
        return table

if __name__ == "__main__":
    cherrypy.server.socket_host = "127.0.0.1"
    cherrypy.server.socket_port = 8080
    config = {
              "/static":
                {"tools.staticdir.on": True,
                 "tools.staticdir.dir": os.getcwd(),
                },
              "/images":
                {"tools.staticdir.on": True,
                 "tools.staticdir.dir": os.getcwd()
                }
             }

    cherrypy.tree.mount(GreatSet(), "/", config=config)
    cherrypy.engine.start()
    cherrypy.engine.block()