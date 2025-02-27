# import the required library
from selenium import webdriver
from selenium.webdriver.common.by import By 
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from datetime import datetime

startTime = datetime.now()

link = 'https://genius.com/Devon-again-never-goes-away-lyrics'

# initialize an instance of the chrome driver (browser)
options = Options()
options.add_argument('-headless')
geckodriver_path = '/Users/masonballard/Desktop/Github-Projects/this-sounds-like/controllers'
driver = webdriver.Firefox(options=options)

driver.get(link)

# soup = BeautifulSoup(driver.page_source, 'html.parser')

# title = soup.find('h1', class_='header_with_cover_art-primary_info-title').get_text()
# artist = soup.find('a', class_='header_with_cover_art-primary_info-primary_artist').get_text()

# print(repr(title))
# print(repr(artist))

links = []
images = driver.find_elements(By.CLASS_NAME, 'SizedImage-sc-39a204ed-1')
for i in images:
    links.append(i.get_attribute('src'))

print(links)
# artist = driver.find_element(By.CLASS_NAME, 'header_with_cover_art-primary_info-primary_artist')
# print(artist.get_attribute('src'))

# print(repr(title))
# print(repr(artist))

# release the resources allocated by Selenium and shut down the browser
driver.quit()

endTime = datetime.now()

print(f"Program time: {(endTime-startTime).total_seconds()} seconds")