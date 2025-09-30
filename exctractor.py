import re
import sqlite3
from pprint import pprint

conn = sqlite3.connect('songs.db')
cursor = conn.cursor()
cursor.execute('PRAGMA case_sensitive_like=ON')

def _song_formatter(song: str) -> dict:
    """
    Парсит всю информацию о песне
    :param song: запись песни в БД
    :return: словарь с отформатированными данными
    """
    name = song[1]
    cover = song[3]
    description = song[4]
    language = song[5]
    release_year = song[6]
    lyrics = song[8]

    artist = cursor.execute(f'SELECT * FROM artists where ID = {song[2]}').fetchall()[0]
    album = cursor.execute(f'SELECT * FROM albums where ID = {song[2]}').fetchall()[0]

    album_name = album[1]
    album_cover = album[2]

    artist_name = artist[1]
    artist_image = artist[2]
    artist_description = artist[3]


    return {
        'name': name,
        'cover': cover,
        'description': description,
        'language': language,
        'release_year': release_year,
        'lyrics': lyrics,
        'album': {
            'name': album_name,
            'cover': album_cover
        },
        'artist': {
            'name': artist_name,
            'image': artist_image,
            'description': artist_description
        }
    }


def _artist_formatter(artist_id: str, parse_songs: bool = False) -> dict:
    """
    Форматирует данные об артисте
    :param artist_id: ID артиста из БД
    :param parse_songs: добавить или нет песни (и их текст)
    :return:
    """
    art = cursor.execute('SELECT * FROM artists WHERE ID = ?', (artist_id,)).fetchone()
    data = {
        'name': art[1],
        'image': art[2],
        'description': art[3]
    }
    if parse_songs:
        data['songs'] = [
            _song_formatter(song) for song in cursor.execute("""
            SELECT * FROM songs WHERE artist_id = ?
            """, (art[0],)).fetchall()
        ]
    return data


def FindByYear(year: int) -> list:
    """
    Находит все песни, вышедшие за указанный год
    :param year: год, за который надо найти песни
    :return: возвращает отформатированный список песен за год
    """
    songs = cursor.execute(f"SELECT * FROM songs WHERE release_year = {year}").fetchall()

    data = []
    for song in songs:
        data.append(_song_formatter(song))

    return data


def FindByAlbum(album_name: str) -> list[dict]:
    """
    Находит альбомы
    :param album_name: название альбома
    :return: возвращает список альбомов
    """

    albums = cursor.execute(f"""SELECT *
    FROM albums
    WHERE LOWER(title) LIKE LOWER('%' || ? || '%');
    """, (album_name,)).fetchall()

    albums += cursor.execute(f"""SELECT *
    FROM albums
    WHERE LOWER(title) LIKE LOWER('%' || ? || '%');
    """, (album_name.capitalize(),)).fetchall()

    albums = [al[1:] for al in albums]
    albums = set(albums)
    albums = list(albums)
    data = []
    for album in albums:
        name = album[0]
        image = album[1]
        album_id = album[2]
        artist = cursor.execute("SELECT * FROM artists WHERE ID = ?", (album_id,)).fetchone()
        songs = [_song_formatter(song) for song in
                      cursor.execute("""SELECT * FROM 
                      songs WHERE album_id = ?""", (str(album_id),))
                      .fetchall()]
        data.append({
            'name': name,
            'artist': _artist_formatter(artist[0]),
            'image': image
        })

    return data


def FindByTitle(title: str) -> list:
    """
    Ищет по названию песни (при этом ключевое слово поиска может быть внутри слова)
    :param title: название песни
    :return:
    """

    # очищает строку от ненужных символов
    title = re.sub(r"\(.*\)", "", title).strip().lower()
    # на английском - игнорирует регистр
    # на русском - не игнорирует


    # 2 запроса в БД, так как sqlite ВИДИТ отличия между "у" и "У" (рус) (и это не отключить)
    # но при этом между "y" и "Y" (англ) не видит

    songs = cursor.execute(f"""SELECT *
FROM songs
WHERE LOWER(name) LIKE LOWER('%' || ? || '%');
""", (title,)).fetchall()

    songs += cursor.execute(f"""SELECT *
FROM songs
WHERE LOWER(name) LIKE LOWER('%' || ? || '%');
""", (title.capitalize(),)).fetchall()

    songs = set(songs)
    data = []
    for song in songs:
        data.append(_song_formatter(song))

    return data


def ShowArtists(name: str) -> list | None:
    """
    Ищет всех артистов по имени
    :param name:
    :return:
    """
    title = re.sub(r"\(.*\)", "", name).strip().lower()
    # на английском - игнорирует регистр
    # на русском - не игнорирует

    # 2 запроса в БД, так как sqlite ВИДИТ отличия между "у" и "У" (рус) (и это не отключить)
    # но при этом между "y" и "Y" (англ) не видит

    artist = cursor.execute(f"""SELECT *
FROM artists
WHERE LOWER(name) LIKE LOWER('%' || ? || '%');
""", (title,)).fetchall()

    artist += cursor.execute(f"""SELECT *
FROM artists
WHERE LOWER(name) LIKE LOWER('%' || ? || '%');
""", (title.capitalize(),)).fetchall()

    artist = set(artist)
    artist = list(artist)

    if artist:
        data = []
        for ar in artist:
            data.append(_artist_formatter(ar[0], True))
        return data

    else:
        return None


if __name__ == '__main__':
    d = FindByYear(int(input("Поиск по году выхода песни: ")))
    for song in d:
        print(f"{song['name']}")
