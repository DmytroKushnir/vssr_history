import re
import os
import sqlite3
from itertools import repeat
from jellyfish import jaro_winkler

db_name = 'brm.db'


def clean_name(s: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z ]', '', s.strip().upper()))


def conver_result(s: str) -> int:
    lst = re.findall(r'\d+\D+\d+', s)
    if lst:
        tm = re.findall(r'\d+', lst[0])
        return 60 * int(tm[0]) + int(tm[1])
    else:
        return 0


def get_riders():
    return [row for row in cursor.execute('SELECT * FROM riders')]


def find_best_match(new_name: str, threstold=0.8):

    def gen_riders():
        for i, n in riders:
            yield from zip(repeat(i), n.split('|'))

    res = []

    for rd_id, rd_name in gen_riders():
        sml = jaro_winkler(new_name, rd_name)

        if sml < 1:
            if sml > threstold:
                res.append((sml, rd_id, rd_name))
        else:
            return True, (1, rd_id, rd_name)

    return False, sorted(res, reverse=True)


def add_new_rider(new_name: str) -> int:
    cursor.execute(f"INSERT INTO riders ('rider_names') VALUES ('{new_name}')")
    r_id = cursor.lastrowid
    return r_id


def update_rider(r_id: int, new_name: str) -> int:
    cursor.execute(f"UPDATE riders SET rider_names = rider_names || '|{new_name}' WHERE rider_id = {r_id}")
    r_id = cursor.lastrowid
    return r_id


def get_rider_id(new_name: str) -> int:

    is_match, match_list = find_best_match(new_name)

    if is_match:
        print(f'{new_name} - exist')
        return match_list[1]
    else:
        if match_list:
            print(f'\n\n    {new_name}\n--------------------')
            for k, m in enumerate(match_list):
                print(f'{k} - {m[2]} ({m[1]}) - {str(m[0])[:5]}')
            choice = input()
            if choice:
                update_rider(match_list[int(choice)][1], new_name)
                return match_list[int(choice)][1]
            else:
                return add_new_rider(new_name)
        else:
            print(f'{new_name} - added')
            return add_new_rider(new_name)


def process_brevet(file_name: str):

    global riders, cursor

    brevet_date, distance, *title = os.path.splitext(os.path.split(file_name)[1])[0].split(' ')
    title = ' '.join(title)
    distance = int(distance)

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(f"INSERT OR REPLACE INTO brevets VALUES ('{brevet_date}', {distance}, '{title}')")

        riders = get_riders()

        with open(file_name) as f1:
            for line in f1:
                l1, l2 = line.split(',')
                rider_name = clean_name(l1)
                result = conver_result(l2)
                rider_id = get_rider_id(rider_name)

                cursor.execute(f"INSERT OR REPLACE INTO results VALUES ('{brevet_date}', {rider_id}, {result})")

        conn.commit()
