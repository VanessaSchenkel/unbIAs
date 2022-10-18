"""Usage:
    generate_translations.py --sentence=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt
import more_itertools

# Local imports
from translation_google import translate_text
from spacy_utils import get_pronoun_on_sentence, get_nlp_en, get_sentence_gender, get_nsubj_sentence, get_nlp_pt, format_sentence, split_sentences_by_nsubj
from generate_model_translation import generate_translation, get_constrained_translation_one_subject, get_best_translation, get_contrained_translation
from gender_inflection import get_gender_inflections, get_just_possible_words, format_sentence_inflections
from constrained_beam_search import get_constrained_sentence, get_format_translation
from generate_neutral import make_neutral_with_pronoun


def get_source_sentence(source_sentence):
    if ' ' not in source_sentence.strip():
        translation = generate_translation(source_sentence)
        formatted =  translation.rstrip(".")
        formatted_translation = get_nlp_pt(formatted)
        possible_words = get_just_possible_words(formatted_translation)
        
        return {'possible_words': possible_words[0]}
    else:
        source_sentence = get_nlp_en(source_sentence)
        subjects = get_nsubj_sentence(source_sentence)
        pronoun_list = get_pronoun_on_sentence(source_sentence)
        gender = get_sentence_gender(source_sentence)


        if len(set(pronoun_list)) == 1 and len(set(subjects)) == 1:
            return generate_translation_for_one_subj(
                source_sentence.text_with_ws)

        elif len(gender) == 0 and len(set(pronoun_list)) == 0:
            return generate_translation_for_neutral(source_sentence)

        elif len(subjects) == len(set(pronoun_list)) and len(subjects) > 1:
            return generate_translation_for_more_than_one_gender(source_sentence, subjects)



def generate_translation_for_one_subj(source_sentence):
    translation_google = get_nlp_pt("O médico terminou seu trabalho")
    subject = get_nsubj_sentence(translation_google)
    constrained_sentence = get_constrained_sentence(
        translation_google, subject)
    more_likely, less_likely = get_constrained_translation_one_subject(
        source_sentence, constrained_sentence)
    neutral = make_neutral_with_pronoun(more_likely)
    return {'more_likely': more_likely, 'less_likely': less_likely, 'neutral': neutral}


def generate_translation_for_neutral(source_sentence):
    translation = generate_translation(source_sentence.text)
    translation = get_nlp_pt(translation)
    possible_words = get_just_possible_words(translation)
    sentences = format_sentence_inflections(possible_words)

    return sentences


def generate_translation_for_more_than_one_gender(source_sentence, subjects):
    sentence = format_sentence(source_sentence)
    splitted_list = []
    for sent in sentence:
        sent = get_nlp_en(sent)
        splitted_list.append(split_sentences_by_nsubj(sent, subjects))
    
    collapsed = list(more_itertools.collapse(splitted_list))

    translation = generate_contrained_translation(collapsed)
    format_translation = get_format_translation(translation)
    print(format_translation)

    return ""

def get_google_translation(sentence):
    if "doctor" in sentence:
        return get_nlp_pt("O médico terminou seu trabalho")
    elif "nurse" in sentence:
        return get_nlp_pt(", a enfermeira ainda estava de folga")

def generate_contrained_translation(sentences_splitted):
    translation = ""
    for sentence in sentences_splitted:
        traslation_google_splitted = get_google_translation(sentence)

        nsub_google = get_nsubj_sentence(traslation_google_splitted)

        constrained_sentence = get_constrained_sentence(traslation_google_splitted, nsub_google)

        translation_contrained = get_contrained_translation(sentence, constrained_sentence)
        translation += translation_contrained
    
    return translation     

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
