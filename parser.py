import requests.exceptions
from dotenv import dotenv_values
from lyricsgenius import Genius
from urllib3.exceptions import HTTPError, ReadTimeoutError

ENV = dotenv_values('.env')
AUTH_KEY = ENV['AUTH_KEY']

with open('artists', encoding='utf-8') as f:
    """ перебирает всех артистов, групп из файла artists"""
    genius = Genius(AUTH_KEY)
    for name in f.readlines():
        name = name.replace('\n','')
        try:
            artist = genius.search_artist(name)

        except HTTPError as e:
            print(e.errno)
            print(e.args[0])
            print(e.args[1])
            continue

        except (requests.exceptions.Timeout, TimeoutError,ReadTimeoutError, ConnectionError, requests.exceptions.ConnectionError, AttributeError):
            # пропускает парсинг при таймауте
            print(f"таймаут, {name} пропускается...")
            continue

        artist.save_lyrics(filename=f'{name}.json', ensure_ascii=False)