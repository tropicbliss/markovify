import random
import operator
import bisect
import json
import sqlite3
import os
import shelve
import uuid
from .util import word_join, word_split


class DatabaseError(Exception):
    pass


class ParamError(Exception):
    pass


BEGIN = "___BEGIN__"
END = "___END__"


def accumulate(iterable, func=operator.add):
    it = iter(iterable)
    total = next(it)
    yield total
    for element in it:
        total = func(total, element)
        yield total


def compile_next(next_dict):
    words = list(next_dict.keys())
    cff = list(accumulate(next_dict.values()))
    return [words, cff]


class Chain:
    def __init__(self, state_size, path):
        if state_size < 1:
            raise ParamError("state_size cannot be less than 1")
        self.state_size = state_size
        self.path = path

    def build(self, path):
        filename = f"model-{uuid.uuid1()}.tmp"
        with shelve.open(filename, writeback=True) as db:
            with open(path, 'r') as input_file:
                for line in input_file:
                    line = line.strip()
                    words = word_split(line)
                    items = ([BEGIN] * self.state_size) + words + [END]
                    for i in range(len(words) + 1):
                        state = tuple(items[i: i + self.state_size])
                        raw_state = word_join(state)
                        follow = items[i + self.state_size]
                        if raw_state not in db:
                            db[raw_state] = {}
                        mut_value = db[raw_state]
                        if follow not in mut_value:
                            mut_value[follow] = 0
                        mut_value[follow] += 1

            try:
                os.remove(self.path)
            except FileNotFoundError:
                pass
            conn = sqlite3.connect(self.path)
            cursor = conn.cursor()
            cursor.execute('PRAGMA synchronous = OFF')
            cursor.execute('''
                CREATE TABLE data (
                    key TEXT PRIMARY KEY,
                    words TEXT NOT NULL,
                    cum_freq TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
                );
            ''')
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("INSERT INTO metadata (key, value) VALUES (?, ?)",
                           ("state_size", self.state_size))
            for state, next_dict in db.items():
                raw_key = state
                value = compile_next(next_dict)
                raw_words = json.dumps(value[0])
                raw_cum_freq = json.dumps(value[1])
                cursor.execute("INSERT INTO data (key, words, cum_freq) VALUES (?, ?, ?)",
                               (raw_key, raw_words, raw_cum_freq))
            conn.commit()
            cursor.execute('PRAGMA synchronous = ON')
            conn.close()
        os.remove(filename)

    def move(self, state, cursor):
        choices, cumdist = index_into_state(state, cursor)
        r = random.random() * cumdist[-1]
        selection = choices[bisect.bisect(cumdist, r)]
        return selection

    def walk(self):
        result = []
        state = (BEGIN,) * self.state_size
        conn = get_connection(self.path)
        cursor = conn.cursor()
        while True:
            next_word = self.move(state, cursor)
            if next_word == END:
                break
            result.append(next_word)
            state = tuple(state[1:]) + (next_word,)
        return result

    @classmethod
    def from_db(cls, path):
        conn = get_connection(path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM metadata WHERE key = ?", ("state_size",))
        row = cursor.fetchone()
        conn.close()
        if row:
            state_size = row[0]
        else:
            raise DatabaseError("Invalid database file")
        return cls(state_size, path=path)


def index_into_state(state, cursor):
    raw_state = word_join(state)
    cursor.execute(
        "SELECT words, cum_freq FROM data WHERE key = ?", (raw_state,))
    row = cursor.fetchone()
    if row:
        raw_words = row[0]
        raw_cum_freq = row[1]
    else:
        raise KeyError
    words = json.loads(raw_words)
    cum_freq = json.loads(raw_cum_freq)
    return words, cum_freq


def get_connection(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
