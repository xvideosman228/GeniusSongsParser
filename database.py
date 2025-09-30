import sqlite3
import json
import os, re

import requests.exceptions
from dotenv import dotenv_values
from lyricsgenius import Genius
from urllib3.exceptions import HTTPError, ReadTimeoutError

ENV = dotenv_values('.env')
AUTH_KEY = ENV['AUTH_KEY']

# перебирает все json'ы и читает их
jsons = os.listdir('.')
jsons = [x for x in jsons if re.match(r'.*\.json', x)]

conn = sqlite3.connect('songs.db')
cursor = conn.cursor()

def AddToDatabase(artist_name: str):
    genius = Genius(AUTH_KEY, timeout=20)
    artist_name = artist_name.replace('\n', '')
    try:
        artist = genius.search_artist(artist_name)
        print(f'{artist_name} === ')
        artist.save_lyrics(filename=f'{artist_name}.json', ensure_ascii=False)

    except HTTPError as e:
        print(e.errno)
        print(e.args[0])
        print(e.args[1])

    except (requests.exceptions.Timeout, TimeoutError, ReadTimeoutError, ConnectionError,
            requests.exceptions.ConnectionError, AttributeError):

        # пропускает парсинг при таймауте
        print(f"таймаут, {artist_name} пропускается...")

    else:
        artist.save_lyrics(filename=f'{artist_name}.json', ensure_ascii=False)

        try:
            with open(f'{artist_name}.json', 'r', encoding='utf-8') as f:
                parsed = json.load(f)
            # инфо об артисте
            artist_name = parsed.get('name', '')
            artist_description = parsed.get('description', {}).get('plain', '')
            artist_image = parsed.get('image_url', '')

            cursor.execute("INSERT OR IGNORE INTO artists (name, image, description) VALUES (?, ?, ?)",
                           (artist_name, artist_image, artist_description))

            artist_id = cursor.execute("SELECT id FROM artists WHERE name = ?", (artist_name,)).fetchone()[0]

            # парсит все песни
            for song in parsed.get('songs', []):
                name = song.get('title', '')
                cover = song.get('song_art_image_url', '')
                description = song.get('description', {}).get('plain', '')
                lyrics = song.get('lyrics', '?')

                # если указана дата выхода песни
                release_year = ''
                if 'release_date_components' in song and isinstance(song['release_date_components'], dict):
                    release_year = str(song['release_date_components'].get('year', ''))

                # инфо об альбоме
                album = song.get('album', {})
                album_name = album.get('name', '') if album else ''
                album_cover = album.get('cover_art_url', '') if album else ''

                if album_name:
                    cursor.execute("INSERT OR IGNORE INTO albums (title, cover, artist_id) VALUES (?, ?, ?)",
                                   (album_name, album_cover, artist_id))
                    album_id = cursor.execute("SELECT id FROM albums WHERE title = ?", (album_name,)).fetchone()[0]
                else:
                    album_id = None

                language = song.get('language', '')

                cursor.execute(
                    "INSERT OR IGNORE INTO songs (name, artist_id, cover, description, language, release_year, album_id, lyrics) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, artist_id, cover, description, language, release_year, album_id, lyrics))

            conn.commit()
            print(f"{artist_name} добавлен в БД.")

        except Exception as e:
            print(f"ошибка: {e}")

        else:
            os.remove(f'{artist_name}.json')

        finally:
            conn.close()


if __name__ == '__main__':
    AddToDatabase('rammstein')