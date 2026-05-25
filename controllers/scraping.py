import requests
import sqlite3
from bs4 import BeautifulSoup
from controllers.data import get_db_connection
import json

ALBUM_INFO_DIV_CLASS = "header_with_cover_art-primary_info"
ALBUM_TRACK_LINEITEM = "chart_row-content"
TRACK_INFO_DIV_CLASS = 'SongHeader-desktop__SongDetails-sc-94bfcc83-6'
TRACK_CREDITS_DIV_CLASS = 'Credit__Container-sc-96426b7f-0'


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
      album_info = soup.find('div', class_=ALBUM_INFO_DIV_CLASS)
      album_title = album_info.find('h1').get_text().strip()
      artist = album_info.find('h2').get_text().strip()
    except:
      return 404

    # Found elements looking for
    conn = get_db_connection()
    if (conn.execute(f"SELECT COUNT(*) FROM Albums Where title='{album_title}' and artist='{artist}'").fetchone()[0]) != 0:
      conn.close()
      return 200

    # Doesn't already exist --> Add data to db
    conn.execute('INSERT INTO Albums (title, artist, link) VALUES (?, ?, ?)', (album_title, artist, link))
    conn.commit()
    album_id = conn.execute(f"SELECT id FROM Albums WHERE title = '{album_title}' ;").fetchone()[0]

    tracks = soup.find_all('a', class_='u-display_block')
    for t in tracks:
        title = t.get_text().lstrip().splitlines()[0]
        track_link = t.get('href')
        conn.execute('INSERT INTO Tracks (title, link, album_id) VALUES (?, ?, ?)', (title, track_link, album_id))
        conn.commit()
        track_id = conn.execute(f'SELECT id FROM Tracks WHERE title = "{title}" and album_id={album_id};').fetchone()[0]
        
        req = requests.get(track_link)
        soup = BeautifulSoup(req.content, 'html.parser')
        roll = soup.find_all('div', class_=TRACK_CREDITS_DIV_CLASS)
        for r in roll:
            line = r.get_text(separator='\n')
            field = line.split('\n')[0]
            names = ''.join(line.split('\n')[1:])
            if 'video' not in field.lower():
              conn.execute("INSERT INTO Credits (field, names, track_id) VALUES (?, ?, ?)", (field, names, track_id))
              conn.commit()
        print(f'Got track: {title}')
    print(f'Got album: {album_title}')
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
        title = soup.find('h1', class_ = TRACK_INFO_DIV_CLASS).get_text()
        artist = soup.find('div', class_ = TRACK_INFO_DIV_CLASS).get_text()
        roll = soup.find_all('div', class_ = TRACK_CREDITS_DIV_CLASS)
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

def getAlbumArtLinks(link):
  req = requests.get(link)
  soup = BeautifulSoup(req.content, 'html.parser')
  
  meta = soup.find_all('meta')
  for m in meta:
    if m['content'].find("quot") != -1:
      meta = m['content']
  
  obj = json.loads(meta)
  covers = obj['album']['cover_arts']
  cover_links = []
  for c in covers:
    if c['image_url'] not in cover_links:
      cover_links.append(c['image_url'])
  
  return cover_links

def getSongArtLink(link):
  req = requests.get(link)
  soup = BeautifulSoup(req.content, 'html.parser')

  script = soup.find_all('script')
  for s in script:
    if s.get_text().find('window.__PRELOADED_STATE__') != -1:
      script = s.get_text()
        
  preloaded_state = script.split(');\n    ')[0]
  kw = r"\\n      window.__PRELOADED_STATE__ = JSON.parse(\\"
  preloaded_state=json.loads(preloaded_state[len(kw)-3:-1].replace(r'\"',r'"' ).replace(r'\\"', r'\"').replace(r"\'", r"'").replace(r'\$', r'$'))
  cover_links = []
  for song in preloaded_state['entities']['songs']:
    if 'songArtImageUrl' in preloaded_state['entities']['songs'][song].keys():
      if preloaded_state['entities']['songs'][song]['songArtImageUrl'] not in cover_links:
        cover_links.append(preloaded_state['entities']['songs'][song]['songArtImageUrl'])
  
  return cover_links

def getArtwork(link):
  '''
  USING SELENIUM
  options = Options()
  options.add_argument('-headless')
  # geckodriver_path = '/Users/masonballard/Desktop/Github-Projects/this-sounds-like/controllers'
  driver = webdriver.Firefox(options=options)

  driver.get(link)

  artwork = []
  if link.find('genius.com/albums/') != -1:
    images = driver.find_elements(By.CLASS_NAME, 'cover_art-image')
    for i in images:
      artwork.append(i.get_attribute('src'))
      # print(i.get_attribute('src'))
  else:
    image = driver.find_element(By.CLASS_NAME, 'SizedImage-sc-39a204ed-1')
    artwork.append(image.get_attribute('src'))
    # print(image.get_attribute('src'))

  driver.quit()
  
  return artwork
  '''
  if link.find('albums/') != -1:
    return getAlbumArtLinks(link)
  return getSongArtLink(link)