"""Usage:
    gender_inflection.py --word=WORD [--debug]
"""
# External imports
import logging
from docopt import docopt
import pandas as pd
import json
import ast


import csv


def get_gender_inflections(word: str):
    word = word.rstrip(".")
    is_plural = word.endswith("s")
    if is_plural:
        word = word.rstrip("s")

    matches = []
    with open('./data/pt-inflections-ordered.csv', newline='') as users_csv:
        user_reader = csv.DictReader(users_csv)
        for row in user_reader:
            if row['word'] == word.lower():
                matches.append(row)

    matches_complete = []

    for match in matches:
        new_obj = {}
        pos = match['pos']

        form = match['forms']
        obj = ast.literal_eval(form)

        word_forms = []
        for item in obj:
            if is_plural:
                if 'plural' in item['tags']:
                    word_forms.append(item['form'])
            else:
                if 'plural' not in item['tags']:
                    word_forms.append(item['form'])

        new_obj[pos] = word_forms
        matches_complete.append(new_obj)

    print(matches_complete)


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    word_fn = args["--word"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    get_gender_inflections(word_fn)

    logging.info("DONE")
