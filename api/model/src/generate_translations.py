"""Usage:
    generate_translations.py --st=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt


# Local imports
from translation_google import translate_text
from spacy_utils import get_pronoun_on_sentence, get_nlp_en, get_sentence_gender, get_nsubj_sentence


def get_source_sentence(source_sentence):
    print(source_sentence)
    if ' ' not in source_sentence.strip():
        has_gender = has_gender(source_sentence)
        translate_text(source_sentence)
    else:
        source_sentence = get_nlp_en(source_sentence)
        pronoun_list = get_pronoun_on_sentence(source_sentence)
        print(pronoun_list)

        sentence_gender = get_sentence_gender(source_sentence)
        print("sentence gender", print(sentence_gender))

        subjects = get_nsubj_sentence(source_sentence)
        print("sentence nsubj", print(subjects))

        has_one_gender = has_one_gender_and_one_subject(source_sentence)
        print("has_one_gender", has_one_gender)


def has_one_gender_and_one_subject(sentence):
    subjects = get_nsubj_sentence(source_sentence)
    pronoun_list = get_pronoun_on_sentence(sentence)

    return len(set(pronoun_list)) == 1 and len(set(subjects)) == 1


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    st_fn = args["--st"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    get_source_sentence(st_fn)

    logging.info("DONE")
