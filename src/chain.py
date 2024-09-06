import random
import operator
import bisect
import json
import sqlite3
import os
from .util import word_join


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

    def build(self, corpus):
        model = {}
        for run in corpus:
            items = ([BEGIN] * self.state_size) + run + [END]
            for i in range(len(run) + 1):
                state = tuple(items[i: i + self.state_size])
                follow = items[i + self.state_size]
                if state not in model:
                    model[state] = {}
                if follow not in model[state]:
                    model[state][follow] = 0
                model[state][follow] += 1

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
            value INTEGER
            );
        ''')
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("INSERT INTO metadata (key, value) VALUES (?, ?)",
                       ("state_size", self.state_size))
        for (state, next_dict) in model.items():
            key = state
            value = compile_next(next_dict)
            raw_key = word_join(key)
            raw_words = json.dumps(value[0])
            raw_cum_freq = json.dumps(value[1])
            cursor.execute("INSERT INTO data (key, words, cum_freq) VALUES (?, ?, ?)",
                           (raw_key, raw_words, raw_cum_freq))
        conn.commit()
        cursor.execute('PRAGMA synchronous = ON')
        conn.close()

    def move(self, state, cursor):
        choices, cumdist = index_into_state(state, cursor)
        r = random.random() * cumdist[-1]
        selection = choices[bisect.bisect(cumdist, r)]
        return selection

    def gen(self):
        state = (BEGIN,) * self.state_size
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        while True:
            next_word = self.move(state, cursor)
            if next_word == END:
                break
            yield next_word
            state = tuple(state[1:]) + (next_word,)

    def walk(self):
        return list(self.gen())

    @classmethod
    def from_db(cls, path):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM metadata WHERE key = ?", ("state_size",))
        row = cursor.fetchone()
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
