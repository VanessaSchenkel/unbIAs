"""Usage:
    translate_sentences_wino.py [--debug]
"""

# External imports
import logging
from docopt import docopt
from generate_translations_for_score import generate_translations_for_score
from spacy_utils import get_nlp_en, get_nlp_pt, get_sentence_with_punctuation, get_translation_with_punctuation
from split_sentence import split_on_punctuation

# Local imports


def generate_translations_wino():    
    english_sentences = get_english_sentences_bleu()
    google_translation = get_google_translations()
    translations = []
    start = 1166
    end = 1200
    
    for index in range(start, end):
        sent_english = split_on_punctuation(english_sentences[index])
        sent_trans = split_on_punctuation(google_translation[index])
        translations = ""
        for ind, sentence in enumerate(sent_english):
            source_sentence = get_sentence_with_punctuation(sentence)
            translation_google = get_translation_with_punctuation(sent_trans[ind])
            
            print("===== SOURCE =====>", source_sentence)
            print("===== GOOGLE =====>", translation_google)
            print("-----------------------")
            translation = generate_translations_for_score(source_sentence, translation_google)
            translations += translation + " "
            print(":::::::::TRANSLATION WINO:::::::::::::::", translation)
            print("-----------------------")

        name_file = './data_score/model-en-pt-ted.txt'
        with open(name_file, 'a') as gen_file:
            gen_file.write(translations.strip())
            gen_file.write("\n") 
       

def get_google_translations():
    portuguese_sentences = []

    with open('./data_score/pt-ted-google.txt') as sentences: 
        for line in sentences:
            portuguese_sentences.append(line.strip())

    return portuguese_sentences

def get_english_sentences():
    english_sentences = []

    with open('./data_score/wino/en.txt') as sentences: 
        for line in sentences:
            sp = line.split("\t")
            english_sentences.append(sp[2])

    return english_sentences

def get_english_sentences_pro():
    english_sentences = []

    with open('./data_score/wino/en_pro.txt') as sentences: 
        for line in sentences:
            sp = line.split("\t")
            english_sentences.append(sp[2])

    return english_sentences

def get_english_sentences_anti():
    english_sentences = []

    with open('./data_score/wino/en_anti.txt') as sentences: 
        for line in sentences:
            sp = line.split("\t")
            english_sentences.append(sp[2])

    return english_sentences

def get_english_sentences_bleu():
    english_sentences = []

    with open('./data_score/en-ted.txt') as sentences: 
        for line in sentences:
            english_sentences.append(line.strip())

    return english_sentences


# def generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence, google_translation):
#     translation_nlp = get_nlp_pt(google_translation)
#     people = get_align_people(source_sentence, translation_nlp)
    
#     translation_model = generate_translation(source_sentence)    
#     translation_model_nlp = get_nlp_pt(translation_model)
    
#     subject_source = get_subject_source(source_sentence)
#     source_people = get_people_source(source_sentence)
#     people_model = get_people_model(source_sentence, translation_model_nlp, subject_source)
    
#     people_to_neutral_source = [person.text for person in source_people if person.text != subject_source]
    
#     people_to_neutral, people_google = get_people_to_neutral_and_people_google(source_sentence, translation_nlp, people_to_neutral_source, subject_source)
    
#     people_model_nlp = get_nlp_pt(people_model)
#     people_google_nlp = get_nlp_pt(people_google)
#     model_morph = get_morph(people_model_nlp)
#     model_google = get_morph(people_google_nlp)
    
#     gender_people_model = get_sentence_gender(people_model_nlp)

#     if (people_google == None or len(people_google) == 0) and len(people_model_nlp) > 0:
#         translation_nlp = translation_model_nlp
#     elif len(gender_people_model) > 0 and model_morph != model_google: 
#         constrained_splitted = split_on_subj_and_bsubj(translation_nlp, people)
#         translations = get_translations_with_constrained(source_sentence, constrained_splitted)    
#         translations_aligned_model = get_translations_aligned(translations, constrained_splitted, source_sentence)
#         subj_translated = get_subject_translated_aligned(source_sentence, translations_aligned_model, subject_source)
#         translation_nlp = get_translations_aligned_model_google(translation_nlp, translations_aligned_model, subj_translated)
#     elif people_model == people_google:
#         translation_nlp = combine_translations(translation_nlp, people_google, translation_model_nlp, people_model)
    
#     words_to_neutral, index_to_replace = get_words_to_neutral_and_index_to_replace(translation_nlp, people_to_neutral)
#     inflections = get_just_possible_words(words_to_neutral)
#     first_sentence, second_sentence, third_sentence = format_translations_subjs(index_to_replace, translation_nlp, inflections)
    
#     return first_sentence.replace(".", "").strip() + "."


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    translation = generate_translations_wino()
    print(translation)

    logging.info("DONE")