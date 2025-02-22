from flask import Flask, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import controllers

app = Flask(__name__)

# conn = sqlite3.connect('database.db')
# with open('schema.sql') as f:
#     conn.executescript(f.read())

# ------------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method=='POST':
        albumLink = request.form['link']
        # If form is empty
        if not albumLink:
            return redirect(url_for('index'))
        # If cannot get valid page
        if getAlbum(albumLink) == 404:
            return redirect(url_for('index'))

        conn = scraping.get_db_connection()
        album_id = conn.execute(f'SELECT id FROM Albums WHERE link="{albumLink}";').fetchone()[0]
        # After adding to db to go to getData page
        return redirect(url_for('getData', album_id=album_id))    

    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/getData?<album_id>', methods=['GET'])
def getData(album_id):
    conn = scraping.get_db_connection()
    album = conn.execute(f'SELECT * FROM Albums WHERE id={album_id};').fetchone()
    artwork = scraping.getArtwork(album['link'])
    tracks = conn.execute(f'SELECT * FROM Tracks WHERE album_id={album_id};').fetchall()

    if album['link'].find('album') != -1:
      tracklist = []
      for i, track in enumerate(tracks):
          roll = conn.execute(f"SELECT field, names FROM Credits WHERE track_id={track['id']};").fetchall()
          # 1, Ride, [(field, names), (field, names)...]
          t = [i+1, track['title'], roll]
          tracklist.append(t)

      conn.close()
      return render_template('getData.html', album=album, artwork=artwork, tracklist=tracklist)

    # get song page
    album = {'title':album['title'][7:], 'artist':album['artist']}
    credit = []
    roll = conn.execute(f"SELECT field, names FROM Credits WHERE track_id={tracks[0]['id']};").fetchall()

    for r in roll:
      # Field, (name, ...)
      if (r['field'].find('Released') == -1) and (r['field'].find('Remixes') == -1) and (r['field'].find('Interpolate') == -1):
        names = re.split(', | & ', r['names'])
      else:
        names = [r['names']]
      credit.append((r['field'], names))

    return render_template('getSongData.html', album=album, artwork=artwork, credit=credit)