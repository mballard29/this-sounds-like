import requests
import sqlite3
from bs4 import BeautifulSoup
from controllers.data import get_db_connection

def getAlbum(link):
    if link.find('https://genius.com/albums/') == -1:
      return getSong(link)

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

def getSong(link):
    if link.find('https://genius.com/') == -1:
        return 404

    req = requests.get(link)
    if req.status_code != 200:
        return 404
    
    soup = BeautifulSoup(req.content, 'html.parser')
    title = None
    artist = None
    roll = None
    try:
        # track title, link, album_id
        title = soup.find('h1', class_='SongHeader-desktop-sc-d2837d6d-8').get_text()
        artist = soup.find('div', class_='HeaderArtistAndTracklist-desktop-sc-afd25865-1').get_text()
        roll = soup.find_all('div', class_='SongInfo-sc-4162678b-3')
        call = []
        for r in roll:
          line = r.get_text(separator='\n')
          field = line.split('\n')[0]
          names = ''.join(line.split('\n')[1:])
          call.append((field, names))
    except:
        return 404
            
    conn = get_db_connection()
    if (conn.execute(f"SELECT COUNT(*) FROM Albums Where title='{'Single-'+title}' and artist='{artist}'").fetchone()[0]) != 0:
      conn.close()
      return 200
    
    conn.execute('INSERT INTO Albums (title, artist, link) VALUES (?, ?, ?)', ('Single-'+title, artist, link))
    conn.commit()
    album_id = conn.execute(f"SELECT id FROM Albums WHERE title = '{'Single-'+title}' ;").fetchone()[0]

    conn.execute('INSERT INTO Tracks (title, link, album_id) VALUES (?, ?, ?)', (title, link, album_id))
    conn.commit()
    track_id = conn.execute(f'SELECT id FROM Tracks WHERE title = "{title}" and album_id={album_id};').fetchone()[0]

    for c in call:
      conn.execute("INSERT INTO Credits (field, names, track_id) VALUES (?, ?, ?)", (c[0], c[1], track_id))
      conn.commit()

    conn.close()
    return 200

def getArtwork(link):
    req = requests.get(link)
    soup = BeautifulSoup(req.content, 'html.parser')
    
    art = soup.find('img', class_='SizedImage-sc-39a204ed-2')
    if art != None:
      return art['src']

    art = soup.find('img', class_='cover_art-image')
    if art != None:
      return art['src']

    return None