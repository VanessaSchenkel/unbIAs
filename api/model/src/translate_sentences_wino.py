"""Usage:
    translate_sentences_wino.py [--debug]
"""

# External imports
import logging
from docopt import docopt
import more_itertools
from format_translations import format_translations_subjs
from gender_inflection import get_gender_inflections, get_just_possible_words
from split_sentence import split_on_subj_and_bsubj

# Local imports
from spacy_utils import get_morph, get_nlp_en, get_people_source, get_pronoun_on_sentence, get_nlp_pt, get_sentence_gender
from generate_model_translation import  generate_translation, generate_translation_with_gender_constrained
from constrained_beam_search import  check_constrained_translation,  combine_contrained_translations, get_gender_translations
from roberta import get_disambiguate_pronoun
from word_alignment import get_align_people, get_word_alignment_pairs


def generate_translations_wino():    
    english_sentences = get_english_sentences()
    google_translation = get_google_translations()
    translations = []
    for index, sentence in enumerate(english_sentences):
        print("ENGLISH SENTENCE:", sentence)
        translation_google = google_translation[index]
        print("GOOGLE:", translation_google)
        translation = generate_translation_for_nsubj_and_pobj_with_pronoun(sentence, translation_google)
        print("TRANSLATION:", translation)
        translations.append(translation)
        
        name_file = './data_wino/model-en-pt.txt'

        with open(name_file, 'a') as gen_file:
                gen_file.write(translation)
                gen_file.write("\n")    

def get_google_translations():
    portuguese_sentences = []

    with open('./data_wino/en-pt.txt') as sentences: 
        for line in sentences:
            portuguese_sentences.append(line.strip())

    return portuguese_sentences

def get_english_sentences():
    english_sentences = []

    with open('./data_wino/en.txt') as sentences: 
        for line in sentences:
            sp = line.split("\t")
            english_sentences.append(sp[2])

    return english_sentences

def get_english_sentences_pro():
    english_sentences = []

    with open('./data_wino/en_pro.txt') as sentences: 
        for line in sentences:
            sp = line.split("\t")
            english_sentences.append(sp[2])

    return english_sentences

def get_english_sentences_anti():
    english_sentences = []

    with open('./data_wino/en_anti.txt') as sentences: 
        for line in sentences:
            sp = line.split("\t")
            english_sentences.append(sp[2])

    return english_sentences


def generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence, google_translation):
    source_sentence = get_nlp_en(source_sentence)
    translation_nlp = get_nlp_pt(google_translation)
    people = get_align_people(source_sentence, translation_nlp)
    
    translation_model = generate_translation(source_sentence)
    
    source_nlp = get_nlp_en(source_sentence)
    translation_model_nlp = get_nlp_pt(translation_model)
    people_model = get_align_people(source_nlp, translation_model_nlp)
    
    pronouns = get_pronoun_on_sentence(source_sentence)
    subjects = []
    for pronoun in pronouns:
        subject = get_disambiguate_pronoun(source_sentence, pronoun)
        subjects.append(subject)
    
    sub_split = subjects[0].split()[-1]
    source_people = get_people_source(source_sentence)
    people_to_neutral_source = [person.text for person in source_people if person.text != sub_split]
    alignment_model = get_word_alignment_pairs(source_sentence.text, translation_model_nlp.text, model="bert", matching_methods = "i", align = "itermax")
    people_model = ""
    
    for first_sentence, second_sentence in alignment_model:
      if first_sentence == sub_split:
        people_model = second_sentence
    
    people_to_neutral= []
    
    alignment = get_word_alignment_pairs(source_sentence.text, translation_nlp.text, model="bert", matching_methods = "i", align = "itermax")
    people_google = ""
    
    for first_sentence, second_sentence in alignment:
      if first_sentence in people_to_neutral_source:
        people_to_neutral.append(second_sentence)
      elif first_sentence == sub_split:
          people_google = second_sentence
    
    people_model_nlp = get_nlp_pt(people_model)
    people_google_nlp = get_nlp_pt(people_google)
    
    model_morph = get_morph(people_model_nlp)
    model_google = get_morph(people_google_nlp)
    
    gender_people_model = get_sentence_gender(people_model_nlp)

    if len(gender_people_model) > 0 and model_morph != model_google: 
        constrained_splitted = split_on_subj_and_bsubj(translation_nlp, people)
        translations = []
        
        for constrained in constrained_splitted:
            constrained_translation = generate_translation_with_gender_constrained(source_sentence.text_with_ws, constrained)
            translation = check_constrained_translation(constrained, constrained_translation, source_sentence.text_with_ws)
            
            translations.append(translation)
        
        if len(translations) == 1:
            translations_aligned = translations[0]
        elif len(translations) == 2:
            translations_aligned = combine_contrained_translations(translations, constrained_splitted, source_sentence)
        elif len(translations) > 2:
            translation = ""
            trans_aligned = ""
            for index, translation in enumerate(translations):
                if index == 0:
                    trans_aligned = translations[0]
                elif index < len(translations)-1:
                    next_trans = translations[index+1]
                    trans = [trans_aligned, next_trans]
                    trans_aligned = combine_contrained_translations(trans, constrained_splitted, source_sentence)
                else:
                    translation = combine_contrained_translations([trans_aligned, translations[-1]], constrained_splitted, source_sentence)
                    translations_aligned =  translation
    
        alignment_with_constrained = get_word_alignment_pairs(source_sentence.text, translations_aligned, model="bert", matching_methods = "i", align = "itermax")
        sub_split = subjects[0].split()
        subj_translated = ""
        
        for first_sentence, second_sentence in alignment_with_constrained: 
            if first_sentence in sub_split:
                subj_translated += second_sentence + " "

        alignment_with_translation = get_word_alignment_pairs(translation_nlp.text, translations_aligned, model="bert", matching_methods = "i", align = "itermax")
    
        translated = ""
        subj_translated_split = subj_translated.split()
        for first_sentence, second_sentence in alignment_with_translation: 
            last_word = translated.strip().split(" ")[-1]
            if second_sentence in subj_translated_split and second_sentence != last_word and second_sentence not in translated:
                translated += second_sentence + " "
            elif first_sentence[:-1] != last_word[:-1] or len(translated) == 0:
                translated += first_sentence + " "

        translation_nlp = get_nlp_pt(translated)
    
    elif people_model == people_google:
        head_google = [token for token in translation_nlp if token.head.text == people_google]
        head_model = [token for token in translation_model_nlp if token.head.text == people_model]
        
        gender_head_google = [token.morph.get("Gender").pop() for token in head_google if len(token.morph.get("Gender")) > 0]
        gender_head_model = [token.morph.get("Gender").pop() for token in head_model if len(token.morph.get("Gender")) > 0]
            
        if(set(gender_head_google) != set(gender_head_model)):
            lemmas_google = [token.lemma_ for token in head_google]
            lemmas_model = [token.lemma_ for token in head_model]

            if lemmas_google == lemmas_model:
                google_index = [token.i for token in head_google]
                new_translation = ""

                for token in translation_nlp:
                    for ind in google_index:
                        if token.i == ind:
                            new_translation += head_model.pop(0).text_with_ws
                        else:
                            new_translation += token.text_with_ws

                translation_nlp = get_nlp_pt(new_translation)
        
    words_to_neutral = []
    index_to_replace = []
    for index, token in enumerate(translation_nlp):
            # print(token, "->", token.lemma_,"->", token.head,"->", token.head.lemma_)
            if token.head.text in people_to_neutral or token.head.text[:-1] in people_to_neutral or token.head.lemma_ in people_to_neutral or token.text in people_to_neutral or token.text[:-1] in people_to_neutral or token.lemma_ in people_to_neutral :
                words_to_neutral.append(token)
                index_to_replace.append(index)

    inflections = get_just_possible_words(words_to_neutral)
    first_sentence, second_sentence, third_sentence = format_translations_subjs(index_to_replace, translation_nlp, inflections)
    
    print(first_sentence)
    print(second_sentence)
    print(third_sentence)
    
    return first_sentence.replace(".", "").strip() + "."


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