from flask import Flask, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
from controllers.data import get_db_connection, truncate_tables
from controllers.scraping import getAlbum, getArtwork
import cv2
import numpy as np
from sklearn.cluster import KMeans
import urllib.request
import os

app = Flask(__name__)

# conn = sqlite3.connect('database.db')
# with open('schema.sql') as f:
#     conn.executescript(f.read())

# DYNAMIC STYLING FUNCTIONALITY
def make_histogram(cluster):
    """
    Count the number of pixels in each cluster
    :param: KMeans cluster
    :return: numpy histogram
    """
    numLabels = np.arange(0, len(np.unique(cluster.labels_)) + 1)
    hist, _ = np.histogram(cluster.labels_, bins=numLabels)
    hist = hist.astype('float32')
    hist /= hist.sum()
    return hist

def make_bar(height, width, color):
    """
    Create an image of a given color
    :param: height of the image
    :param: width of the image
    :param: BGR pixel values of the color
    :return: tuple of bar, rgb values, and hsv values
    """
    bar = np.zeros((height, width, 3), np.uint8)
    bar[:] = color
    red, green, blue = int(color[2]), int(color[1]), int(color[0])
    hsv_bar = cv2.cvtColor(bar, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv_bar[0][0]
    return bar, (red, green, blue), (hue, sat, val)

def sort_hsvs(hsv_list):
    """
    Sort the list of HSV values
    :param hsv_list: List of HSV tuples
    :return: List of indexes, sorted by hue, then saturation, then value
    """
    bars_with_indexes = []
    for index, hsv_val in enumerate(hsv_list):
        bars_with_indexes.append((index, hsv_val[0], hsv_val[1], hsv_val[2]))
    bars_with_indexes.sort(key=lambda elem: (elem[1], elem[2], elem[3]))
    return [item[0] for item in bars_with_indexes]

def generateStyles(link):
    req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read()
    arr = np.asarray(bytearray(html), dtype=np.uint8)
    img = cv2.imdecode(arr, -1) # 'Load it as it is'

    # START HERE
    # img = cv2.imread('nwtcdwyaof.png')
    height, width, _ = np.shape(img)

    # reshape the image to be a simple list of RGB pixels
    image = img.reshape((height * width, 3))

    # we'll pick the 5 most common colors
    num_clusters = 3
    clusters = KMeans(n_clusters=num_clusters)
    clusters.fit(image)

    # count the dominant colors and put them in "buckets"
    histogram = make_histogram(clusters)
    # then sort them, most-common first
    combined = zip(histogram, clusters.cluster_centers_)
    combined = sorted(combined, key=lambda x: x[0], reverse=True)

    # finally, we'll output a graphic showing the colors in order
    # bars = []
    # hsv_values = []
    colors = []
    for index, rows in enumerate(combined):
        bar, rgb, hsv = make_bar(100, 100, rows[1])
        colors.append(rgb)
    return colors
    
def genStyles(link):
    if link == None:
    #  rgb(117, 124, 132)
      colors = [(117, 124, 132), (117, 124, 132), (117, 124, 132)]
    else:
      colors = generateStyles(link)

    primary = f'rgba({colors[0][0]}, {colors[0][1]}, {colors[0][2]}, 0.7)'
    solid_primary = f'rgba({colors[0][0]}, {colors[0][1]}, {colors[0][2]}, 1)'
    secondary = f'rgba({colors[1][0]}, {colors[1][1]}, {colors[1][2]}, 0.7)'
    # tertiary = primary = f'rgba({colors[2][0]}, {colors[2][1]}, {colors[2][2]}, 0.7)'
    content = f"""
    /* HEADER */
    .nav-masthead .nav-link {{
      color: rgba(255, 255, 255, 0.9);
      /* border-bottom: .25rem solid transparent; */
    }}
    .nav-masthead .nav-link:hover,
    .nav-masthead .nav-link:focus {{
      border-bottom-color: rgba(255, 255, 255, 0.9);
    }}
    /* .nav-masthead .nav-link + .nav-link {{
      margin-left: 1rem;
    }} */
    .float-md-start {{
      color: rgba(255, 255, 255, 0.9);
    }}
    .nav-masthead .active {{
      color: #ffffffe4;
      border-bottom-color: #ffffffe4;
    }}

    .bd-placeholder-img {{
      font-size: 1.125rem;
      text-anchor: middle;
      -webkit-user-select: none;
      -moz-user-select: none;
      user-select: none;
    }}
    @media (min-width: 768px) {{
      .bd-placeholder-img-lg {{
          font-size: 3.5rem;
      }}
    }}
    .b-example-divider {{
      width: 100%;
      height: 3rem;
      background-color: rgba(0, 0, 0, 0.1);
      border: solid rgba(0, 0, 0, 0.15);
      border-width: 1px 0;
      box-shadow: inset 0 0.5em 1.5em rgba(0, 0, 0, 0.1),
        inset 0 0.125em 0.5em rgba(0, 0, 0, 0.15);
    }}
    .b-example-vr {{
      flex-shrink: 0;
      width: 1.5rem;
      height: 100vh;
    }}
    .bi {{
      vertical-align: -0.125em;
      fill: currentColor;
    }}
    .nav-scroller {{
      position: relative;
      z-index: 2;
      height: 2.75rem;
      overflow-y: hidden;
    }}
    .nav-scroller .nav {{
      display: flex;
      flex-wrap: nowrap;
      padding-bottom: 1rem;
      margin-top: -1px;
      overflow-x: auto;
      text-align: center;
      white-space: nowrap;
      -webkit-overflow-scrolling: touch;
    }}
    [data-bs-theme=dark] {{
      color-scheme: dark;
      --bs-body-bg: {secondary};
    }}

    /* COLOR PICKER */
    .btn-bd-primary {{
      --bd-violet-bg: {solid_primary};
      --bd-violet-rgb: 112.520718, 44.062154, 249.437846;
      --bs-btn-font-weight: 600;
      --bs-btn-color: var(--bs-white);
      --bs-btn-bg: var(--bd-violet-bg);
      --bs-btn-border-color: var(--bd-violet-bg);
      --bs-btn-hover-color: var(--bs-white);
      --bs-btn-hover-bg: {solid_primary};
      --bs-btn-hover-border-color: {primary};
      --bs-btn-focus-shadow-rgb: var(--bd-violet-rgb);
      --bs-btn-active-color: var(--bs-btn-hover-color);
      --bs-btn-active-bg: {solid_primary};
      --bs-btn-active-border-color: {primary};
      --bs-btn-focus-shadow-rgb: {primary}
    }}
    .bd-mode-toggle {{
      z-index: 1500;
    }}
    .bd-mode-toggle .dropdown-menu .active .bi {{
      play: block !important;
    }}
    img {{
      border-radius: 1%;
    }}
    .dropdown-item.active,
    .dropdown-item:active {{
        background-color: {primary};
    }}
    /* For: {link} */
    .navbar {{
      background-color: {primary};
    }}
    """
    f = open("static/css/getDataStyles.css", "w")
    f.write(content)
    f.close()

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
    artwork = getArtwork(album['link'])
    tracks = conn.execute(f'SELECT * FROM Tracks WHERE album_id={album_id};').fetchall()

    if album['link'].find('album') != -1:
      tracklist = []
      for i, track in enumerate(tracks):
          roll = conn.execute(f"SELECT field, names FROM Credits WHERE track_id={track['id']};").fetchall()
          # 1, Ride, [(field, names), (field, names)...]
          t = [i+1, track['title'], roll]
          tracklist.append(t)

      conn.close()
      genStyles(artwork)
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

    genStyles(artwork)
    return render_template('getSongData.html', album=album, artwork=artwork, credit=credit)