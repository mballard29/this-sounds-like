from flask import Flask, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import sqlite3
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# conn = sqlite3.connect('database.db')
# with open('schema.sql') as f:
#     conn.executescript(f.read())

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def truncate_tables():
    conn = get_db_connection()
    conn.execute('DELETE FROM Albums;')
    conn.commit()
    conn.execute('DELETE FROM Tracks;')
    conn.commit()
    conn.execute('DELETE FROM Credits;')
    conn.commit()
    conn.close()

def get_album(link):
    if link.find('https://genius.com/albums/') == -1:
        return 404

    # Got valid link
    req = requests.get(link)
    if req.status_code != 200:
        return 404

    # Got valid page
    soup = BeautifulSoup(req.content, 'html.parser')
    try:
        title = soup.find('h1', class_='header_with_cover_art-primary_info-title').get_text()
        artist = soup.find('a', class_='header_with_cover_art-primary_info-primary_artist').get_text()
    except:
        return 404

    # Found elements looking for
    conn = get_db_connection()
    if (conn.execute(f"SELECT COUNT(*) FROM Albums Where title='{title}' and artist='{artist}'").fetchone()[0]) != 0:
        conn.close()
        return 200

    # Doesn't already exist --> Add data to db
    conn.execute('INSERT INTO Albums (title, artist, link) VALUES (?, ?, ?)', (title, artist, link))
    conn.commit()
    album_id = conn.execute(f"SELECT id FROM Albums WHERE title = '{title}' ;").fetchone()[0]

    tracks = soup.find_all('a', class_='u-display_block')
    for t in tracks:
        title = t.get_text().lstrip().splitlines()[0]
        track_link = t.get('href')
        conn.execute('INSERT INTO Tracks (title, link, album_id) VALUES (?, ?, ?)', (title, track_link, album_id))
        conn.commit()
        track_id = conn.execute(f'SELECT id FROM Tracks WHERE title = "{title}" and album_id={album_id};').fetchone()[0]
        
        req = requests.get(track_link)
        soup = BeautifulSoup(req.content, 'html.parser')
        roll = soup.find_all('div', class_='SongInfo-sc-4162678b-3')
        for r in roll:
            line = r.get_text(separator='\n')
            field = line.split('\n')[0]
            names = ''.join(line.split('\n')[1:])
            conn.execute("INSERT INTO Credits (field, names, track_id) VALUES (?, ?, ?)", (field, names, track_id))
            conn.commit()
            
    conn.close()
    return 200

def getArtwork(link):
    req = requests.get(link)
    soup = BeautifulSoup(req.content, 'html.parser')
    art = soup.find('img', class_='cover_art-image')
    return art['src']

# ------------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method=='POST':
        albumLink = request.form['link']
        # If form is empty
        if not albumLink:
            return redirect(url_for('index'))
        # If cannot get valid page
        if get_album(albumLink) == 404:
            return redirect(url_for('index'))

        conn = get_db_connection()
        album_id = conn.execute(f'SELECT id FROM Albums WHERE link="{albumLink}";').fetchone()[0]
        # After adding to db to go to getData page
        return redirect(url_for('getData', album_id=album_id))    

    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/getData?<album_id>', methods=['GET'])
def getData(album_id):
    conn = get_db_connection()
    album = conn.execute(f'SELECT * FROM Albums WHERE id={album_id};').fetchone()
    # artwork_link = ''
    artwork_link = getArtwork(album['link'])
    tracks = conn.execute(f'SELECT * FROM Tracks WHERE album_id={album_id};').fetchall()

    tracklist = []
    for i, track in enumerate(tracks):
        # get credits
        roll = conn.execute(f"SELECT field, names FROM Credits WHERE track_id={track['id']};").fetchall()
        # 1, Ride, [(field, names), (field, names)...]
        t = [i+1, track['title'], roll]
        tracklist.append(t)

    conn.close()
    return render_template('getData.html', album=album, artwork_link=artwork_link, tracklist=tracklist)