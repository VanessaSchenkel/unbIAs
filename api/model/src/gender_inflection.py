"""Usage:
    gender_inflection.py --word=WORD [--debug]
"""
# External imports
import logging
from docopt import docopt
import ast
import csv
import itertools

from generate_neutral import make_neutral
from spacy_utils import get_nlp_pt, get_word_pos_and_morph


def get_gender_inflections(word: str):
    gender_inflections = {}
    word = word.rstrip(".").lower()
    word = get_nlp_pt(word)
    text, pos, morph = get_word_pos_and_morph(word)
    original_text = text
    gender = str(morph.get("Gender")).lower()
    number = str(morph.get("Number"))

    should_get_plural = 'Plur' in number

    if should_get_plural:
        text = text.rstrip("s")

    matches = get_matches(text, pos)

    if matches is None:
        return "No matches"

    gender_inflections['word'] = original_text
    gender_inflections['pos'] = pos
    forms = matches['forms']
    forms_obj = ast.literal_eval(forms)
    forms_matched = []

    for form in forms_obj:
        if any(gender not in string for string in form['tags']) and form['form'] != original_text:
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
        new_obj['tags'] = ['neutral']
        forms_matched.append(new_obj)

    gender_inflections['forms'] = forms_matched

    return gender_inflections


def get_matches(text, pos):
    with open('./data/pt-inflections-ordered.csv', newline='') as users_csv:
        user_reader = csv.DictReader(users_csv)
        for row in user_reader:
            if row['word'] == text and pos in row['pos'].upper():
                return row
            elif text in row['forms'] and pos in row['pos'].upper():
                forms = row['forms']
                forms_obj = ast.literal_eval(forms)
                for form in forms_obj:
                    if text == form['form']:
                        return row


def format_sentence_inflections(possible_words):
    print(possible_words)
    combined = [j for i in zip(*possible_words) for j in i]

    joined = " ".join(combined)
    splitted_by_dot = joined.split(".")

    first_sentence = splitted_by_dot[0].strip().capitalize() + "."
    second_sentence = splitted_by_dot[1].strip().capitalize() + "."
    third_sentence = splitted_by_dot[2].strip().capitalize() + "."

    # TODO PLURAL
    # TODO SPLIT BY ENTITIES
    # all_combinations = list(itertools.product(*possible_words))
    # print("ALL", all_combinations)

    return {'first_sentence': first_sentence, 'second_sentence': second_sentence, 'third_sentence': third_sentence}


def get_just_possible_words(translation):
    forms_list = []
    for word in translation:
        if word.pos_ == "CCONJ" or word.pos_ == "PUNCT":
            forms_list.append([word.text, word.text, word.text])
        else:
            inflections = get_gender_inflections(word.text.lower())
            print(inflections)
            forms = []
            forms.append(inflections['word'])

            for inflection in inflections['forms']:
                forms.append(inflection['form'])

            forms_list.append(forms)

    return forms_list


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
