import zipfile
import requests

def get_font():
    url = 'http://sourceforge.net/projects/dejavu/files/dejavu/2.37/dejavu-fonts-ttf-2.37.zip'
    r = requests.get(url, allow_redirects=True)
    open('dejavu.zip', 'wb').write(r.content)
    with zipfile.ZipFile('dejavu.zip', 'r') as zip_ref:
        zip_ref.extractall('/Library/Fonts/')

get_font()
