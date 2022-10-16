"""Usage:
    generate_translations.py --sentence=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt

# Local imports
from translation_google import translate_text
from spacy_utils import get_pronoun_on_sentence, get_nlp_en, get_sentence_gender, get_nsubj_sentence, get_nlp_pt
from generate_model_translation import generate_translation, get_constrained_translation_one_subject
from gender_inflection import get_gender_inflections
from constrained_beam_search import get_constrained_sentence


def get_source_sentence(source_sentence):
    if ' ' not in source_sentence.strip():
        translation = generate_translation(source_sentence)
        all_inflections = get_gender_inflections(translation)
        return all_inflections
    else:
        source_sentence = get_nlp_en(source_sentence)
        has_one_gender = has_one_gender_and_one_subject(source_sentence)

        if has_one_gender:
            translation = generate_translation_for_one_subj(
                source_sentence.text_with_ws)
            return translation


def generate_translation_for_one_subj(source_sentence):
    translation_google = get_nlp_pt("O médico terminou seu trabalho")
    subject = get_nsubj_sentence(translation_google)
    constrained_sentence = get_constrained_sentence(
        translation_google, subject)
    more_likely, less_likely = get_constrained_translation_one_subject(
        source_sentence, constrained_sentence)
    print(more_likely, less_likely)


def has_one_gender_and_one_subject(sentence):
    subjects = get_nsubj_sentence(sentence)
    pronoun_list = get_pronoun_on_sentence(sentence)

    return len(set(pronoun_list)) == 1 and len(set(subjects)) == 1


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    sentence_fn = args["--sentence"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    source_sentence = get_source_sentence(sentence_fn)
    print(source_sentence)

    logging.info("DONE")
