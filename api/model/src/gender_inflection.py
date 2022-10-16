"""Usage:
    gender_inflection.py --word=WORD [--debug]
"""
# External imports
import logging
from docopt import docopt
import ast
import csv

from generate_neutral import make_neutral
from spacy_utils import get_nlp_pt, get_word_pos_and_morph


def get_gender_inflections(word: str):
    gender_inflections = {}
    word = word.rstrip(".").lower()
    word = get_nlp_pt(word)
    text, pos, morph = get_word_pos_and_morph(word)

    gender = morph.get("Gender")[0].lower()
    number = morph.get("Number")[0]
    should_get_plural = number == 'Plur'

    if number == 'Plur':
        text = text.rstrip("s")

    matches = get_matches(text, pos)

    if matches is None:
        return "No matches"

    gender_inflections['word'] = matches['word']
    gender_inflections['pos'] = pos
    forms = matches['forms']
    forms_obj = ast.literal_eval(forms)
    forms_matched = []

    for form in forms_obj:
        if any(gender not in string for string in form['tags']):
            if should_get_plural and 'plural' in form['tags']:
                forms_matched.append(form)
            elif not should_get_plural and 'plural' not in form['tags']:
                forms_matched.append(form)

    if gender == 'fem' and len(forms_matched) == 0 and text != matches['word']:
        forms_matched.append(matches['word'])

    if len(forms_matched) > 0:
        neutral = make_neutral(gender_inflections['word'])
        new_obj = {}
        new_obj['form'] = neutral
        new_obj['tags'] = 'neutral'
        forms_matched.append(new_obj)

    gender_inflections['forms'] = forms_matched

    return gender_inflections


def get_matches(text, pos):
    with open('./data/pt-inflections-ordered.csv', newline='') as users_csv:
        user_reader = csv.DictReader(users_csv)
        for row in user_reader:
            if row['word'] == text and row['pos'].upper() == pos:
                return row
            elif text in row['forms'] and row['pos'].upper() == pos:
                forms = row['forms']
                forms_obj = ast.literal_eval(forms)
                for form in forms_obj:
                    if text == form['form']:
                        return row


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    word_fn = args["--word"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    inflections = get_gender_inflections(word_fn)
    print(inflections)

    logging.info("DONE")
