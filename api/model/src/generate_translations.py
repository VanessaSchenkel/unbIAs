"""Usage:
    generate_translations.py --sentence=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt
import more_itertools

# Local imports
from translation_google import get_google_translation
from spacy_utils import get_pronoun_on_sentence, get_pobj, is_plural, get_only_subject_sentence, get_people, get_nlp_en, get_sentence_gender, get_nsubj_sentence, get_nlp_pt, has_gender_in_source, get_noun_chunks
from generate_model_translation import generate_translation_with_constrained, generate_translation_with_gender_constrained, generate_translation, get_constrained_translation_one_subject
from gender_inflection import get_just_possible_words, format_sentence_inflections
from constrained_beam_search import  get_constrained, get_constrained_translation, combine_contrained_translations, split_sentences_by_nsubj, split_on_subj_and_bsubj
from generate_neutral import make_neutral_with_constrained, make_neutral
from roberta import get_disambiguate_pronoun
from format_translations import format_sentence, format_multiple_sentence, format_sentence_more_than_one, should_remove_first_word, format_translations_subjs, should_remove_last_word
from word_alignment import get_word_alignment_pairs

def translate(source_sentence):
    if ' ' not in source_sentence.strip():
        return get_translation_for_one_word(source_sentence)

    source_sentence = get_nlp_en(source_sentence)
    subjects = get_nsubj_sentence(source_sentence)
    pronoun_list = get_pronoun_on_sentence(source_sentence)
    gender = get_sentence_gender(source_sentence)
    pobj_list = get_pobj(source_sentence)
        
    # print("subjects, pronoun, gender", subjects, pronoun_list, gender)

    # for token in source_sentence:
    #     print("---->", token, " | ", token.pos_, " | ", token.dep_, " | ", token.head)

    is_all_same_pronoun = is_all_equal(pronoun_list)
    is_all_same_subject = is_all_equal(subjects)


    if is_all_same_pronoun and is_all_same_subject and len(pronoun_list) > 0:
        if is_neutral(pronoun_list):
            return generate_translation_for_one_subj_neutral(source_sentence)

        return generate_translation_for_one_subj(source_sentence)
       
    if len(gender) == 0 and len(set(pronoun_list)) == 0 and len(subjects) == 0:
        return generate_translation_for_sentence_without_pronoun_and_gender(source_sentence)

    elif len(gender) == 0 and len(set(pronoun_list)) == 0 and len(subjects) > 0:
        return generate_translation_with_subject_and_neutral(source_sentence)    

    elif len(subjects) == len(set(pronoun_list)) and not is_all_same_subject:
        return generate_translation_for_more_than_one_gender(source_sentence)
        
    elif len(set(pronoun_list)) == 1 and all("it" == elem.text for elem in pronoun_list):
        return generate_translation_it(source_sentence)
    
    elif len(subjects) > len(pronoun_list) and len(pobj_list) > 0:
        return generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence)

    elif len(subjects) > len(pronoun_list):
        return generate_translation_more_subjects(source_sentence, subjects)

    else:
        google_trans = get_google_translation(source_sentence.text_with_ws)
        return {"google_translation": google_trans}    


### METHODS
def is_all_equal(list):
    return all(i.text == list[0].text for i in list)

def is_neutral(pronoun_list):
    return len(pronoun_list) == 0 or all("I" == elem.text for elem in pronoun_list) or all("they" == elem.text for elem in pronoun_list)

def generate_translation_for_one_subj_neutral(source_sentence):
    # translation_nlp = get_nlp_pt("ele é um ótimo enfermeiro.")
    translation_nlp = get_google_translation(source_sentence.text_with_ws)        
    
    people = get_people(translation_nlp)
    constrained_splitted = get_constrained_translation(translation_nlp, people)

    if len(constrained_splitted) == 0:
        return generate_neutral_translation(translation_nlp)

    translations = []
    for constrained in constrained_splitted:
        constrained_translation = generate_translation_with_constrained(source_sentence.text_with_ws, constrained)
        translations.append(constrained_translation)

    if len(translations) > 1:
        translation_constrained = combine_contrained_translations(translations, constrained_splitted, source_sentence)
        translation_nlp = get_nlp_pt(translation_constrained)
    else:
        translation_nlp = get_nlp_pt(translations[0])

    possible_words = get_just_possible_words(translation_nlp)
    first_sentence, second_sentence, third_sentence = format_sentence_inflections(possible_words)

    return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence}


def generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence):
    translation_nlp = get_google_translation(source_sentence.text_with_ws)
    # translation_nlp = get_nlp_pt("A desenvolvedora discutiu com a designer porque ela não gostou do design.")
    
    people = get_people(translation_nlp)
    constrained_splitted = split_on_subj_and_bsubj(translation_nlp, people)
    translations = []
    
    for constrained in constrained_splitted:
        constrained_translation = generate_translation_with_gender_constrained(source_sentence.text_with_ws, constrained)
        translations.append(constrained_translation)
    
    if len(translations) > 1:
        translation_constrained = combine_contrained_translations(translations, constrained_splitted, source_sentence)
    else:
        translation_constrained = translations[0]
    
    pronouns = get_pronoun_on_sentence(source_sentence)

    subjects = []
    for pronoun in pronouns:
        subject = get_disambiguate_pronoun(source_sentence, pronoun)
        new_obj = {'pronoun': pronoun.text, 'subject': subject}
        subjects.append(new_obj)

    translations = get_gender_translations(subjects, source_sentence.text_with_ws, translation_constrained, people)

    return translations

def get_gender_translations(subjects, source_sentence, translation_constrained, people):
        word_alignments = get_word_alignment_pairs(source_sentence, translation_constrained, matching_methods="m", align="mwmf")
        subj_translated = ""
        gender_pronoun = ""

        for subject in subjects:
            subj_pronoun = get_nlp_en(subject['pronoun'])
            gender_pronoun = set(get_sentence_gender(subj_pronoun))
            
            for first_sentence, second_sentence in word_alignments:
                if first_sentence in subject['subject']:
                    subj_translated += second_sentence + " "
                elif second_sentence in subject['subject']:
                    subj_translated += first_sentence + " "
        

        translation_subj = get_nlp_pt(subj_translated)
        translation_gender = set(get_sentence_gender(translation_subj))
        
        people_to_neutral = [person.text for person in people if person.text not in subj_translated]
        
        words_to_neutral = []
        translation = get_nlp_pt(translation_constrained)
        index_to_replace = []

        for index, token in enumerate(translation):
            if token.head.text in people_to_neutral or token.text in people_to_neutral:
                words_to_neutral.append(token)
                index_to_replace.append(index)

        inflections = get_just_possible_words(words_to_neutral)

        first_sentence, second_sentence, third_sentence = format_translations_subjs(index_to_replace, translation, inflections)
        
        return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence}        

def get_translation_for_one_word(source_sentence):
    # try:
        translation = generate_translation(source_sentence)
        formatted =  translation.rstrip(".")
        formatted_translation = get_nlp_pt(formatted)
        source = get_nlp_en(source_sentence)
        is_source_plural = is_plural(source)
        is_translation_plural = is_plural(formatted_translation)

        if is_source_plural != is_translation_plural:
            formatted_translation = get_google_translation(source_sentence)
        
        possible_words = get_just_possible_words(formatted_translation)[0]

        possible_words_formatted = [word.capitalize() for word in possible_words]

        return {'possible_words': possible_words_formatted}    
    # except:
    #     return "An error occurred translating one word"

def generate_translation_for_one_subj(source_sentence):
    try:
        translation_google =  get_google_translation(source_sentence.text_with_ws) 
        # translation_google =  get_nlp_pt("Ela é uma boa médica.") 

        subject = get_only_subject_sentence(translation_google)
        print("SUBJECT", subject, subject.pos_)
        if subject.pos_ == 'NOUN':
            constrained_sentence = get_constrained(source_sentence) 
            print("CONSTRAINED:", constrained_sentence) 
            more_likely, less_likely = get_constrained_translation_one_subject(source_sentence.text_with_ws, constrained_sentence)
            neutral = make_neutral_with_constrained(more_likely, constrained_sentence)

            return {"more_likely": more_likely,"less_likely": less_likely ,"neutral": neutral.capitalize()}

        
        constrained_splitted = get_constrained_translation(translation_google, [subject])        
        translations = []

        for constrained in constrained_splitted:
            constrained_translation = generate_translation_with_constrained(source_sentence.text_with_ws, constrained)
            translations.append(constrained_translation)

        if len(translations) > 1:
            translation_constrained = combine_contrained_translations(translations, constrained_splitted, source_sentence, matching_methods = "m", align = "mwmf" )
        else:
            translation_constrained = translations[0]

        neutral =  make_neutral(translation_constrained)

        return {"translation": translation_constrained, "neutral": neutral.capitalize()}

    except:
        return "An error occurred translating for one subject"


def generate_translation_with_subject_and_neutral(source_sentence):
    try:
        translation = generate_translation(source_sentence.text, 2)
        translation_nlp = get_nlp_pt(translation[0])
        neutral = make_neutral(translation_nlp)

        return {"first_option": translation[0], "second_option": translation[1], "neutral": neutral}
    except:
        return "An error occurred translating for one subject without pronoun"  
 
def generate_neutral_translation(translation):
    try:
        possible_words = get_just_possible_words(translation)
        first_option, second_option, neutral = format_sentence_inflections(possible_words)
    
        return {"first_option": first_option, "second_option": second_option, "neutral": neutral}
    except:
        return "An error occurred translating sentence with they"    

def generate_translation_for_sentence_without_pronoun_and_gender(source_sentence):
    try:
        translation = generate_translation(source_sentence.text_with_ws)
        translation = get_nlp_pt(translation)
        possible_words = get_just_possible_words(translation)
        first_option, second_option, neutral = format_sentence_inflections(possible_words)
        
        return {"first_option": first_option, "second_option": second_option, "neutral": neutral}
    except:
        return "An error occurred translating sentence without pronoun and gender"    
 

def generate_translation_for_more_than_one_gender(source_sentence):
    try:
        sentences = format_sentence_more_than_one(source_sentence)
        print("sentences:", sentences)
        translations_more_likely = []
        translations_neutral = []

        for sentence in sentences:
            print("sentence:", sentence)
            should_remove_first = should_remove_first_word(sentence)
            print("should remove:", should_remove_first)
            should_remove_last = should_remove_last_word(sentence[-1])
            print("should remove last:", should_remove_last)
            sentence_to_translate = ""
            word_to_add = ""
            word_to_add_last = ""
            if should_remove_first:
                sentence_to_translate =  sentence.strip().split(' ', 1)[1]
                print("sentence to translate", sentence_to_translate)
                first_word = sentence.strip().split(' ', 1)[0]
                print("first_word", first_word)
                word_to_add = get_word_to_add(first_word) + " "
                print("word_to_add", word_to_add)
            elif should_remove_last:
                sentence_to_translate =  sentence.strip()[:-1]
                print("sentence to translate", sentence_to_translate)
                last_word = sentence.strip().split(' ', 1)[-1]
                print("last_word", last_word)
                word_to_add_last = get_word_to_add(last_word)
                print("word_to_add_last", word_to_add_last)
            else:
                sentence_to_translate = sentence
            
            sentence_to_translate += "."
            sent = get_nlp_en(sentence_to_translate)
            translations = generate_translation_for_one_subj(sent)
            more_likely = word_to_add + translations['more_likely'] + word_to_add_last
            neutral = word_to_add + translations['neutral'] + word_to_add_last
            translations_more_likely.append(more_likely)
            translations_neutral.append(neutral)

        sentence_more_likely = " ".join(translations_more_likely).replace(".", "").lower().capitalize() + "."
        sentence_neutral = " ".join(translations_neutral).replace(".", "").lower().capitalize() + "."

        return {"translation": sentence_more_likely, "neutral": sentence_neutral}
          
    except:
        return "An error occurred translating more than one gender on the sentence"    

def get_word_to_add(word):
    w = get_nlp_en(word)
    for token in w:
        if token.is_punct:
            return token.text

    word_translatted =  generate_translation(word)
    return word_translatted


def generate_translation_more_subjects(source_sentence, subjects):
    try:
        sentence = format_sentence(source_sentence)
        splitted_list = []
        for sent in sentence:
            sent = get_nlp_en(sent)
            splitted_list.append(split_sentences_by_nsubj(sent, subjects))
        
        collapsed = list(more_itertools.collapse(splitted_list))

        translations = []
        for sentence in collapsed:
            has_gender = has_gender_in_source(sentence)
            more_likely, less_likely, neutral =  generate_translation_for_one_subj(sentence)
            
            if has_gender:
                translations.append([more_likely])
            else:
                translations.append([more_likely, less_likely, neutral])

        all_combinations = format_multiple_sentence(translations)

        return all_combinations    
    except:
        return "An error occurred translating more than one subject"        

def generate_translation_it(source_sentence):
    try:
        google_trans = get_google_translation(source_sentence.text_with_ws)
        # google_trans = get_nlp_pt("O troféu não cabia na mala marrom porque era muito grande.")
        it_token = get_nlp_pt("it")
        subj_roberta = get_disambiguate_pronoun(source_sentence, it_token)

        google_trans = get_nlp_pt(google_trans)

        sentence_splitted_source = format_sentence(source_sentence)

        index_it = 0
        index_without_it = 0
        for index, sentence in enumerate(sentence_splitted_source):
            if " it " in sentence:
                index_it = index
            else:
                index_without_it = index

        sentence_splitted_trans = format_sentence(google_trans)
        sentence_pt_with_it = sentence_splitted_trans[index_it]

        noun_chunks_source = get_noun_chunks(source_sentence)
        noun_chunks_pt = get_noun_chunks(google_trans)

        index_subj = 0
        for index, chunk in enumerate(noun_chunks_source):
            if subj_roberta in chunk.text_with_ws:
                index_subj = index
        
        sub = noun_chunks_pt[index_subj]
        gender_sub = get_sentence_gender(sub)
        sentence_pt = get_nlp_pt(sentence_pt_with_it)
        gender_chunk = get_sentence_gender(sentence_pt)
        
        if all(i == gender_sub[0] for i in gender_chunk):
            return  {'translation_it': google_trans }
    
        else:
            possible_words = get_just_possible_words(sentence_pt)
            sentences = format_sentence_inflections(possible_words)
            sentence = sentence_splitted_trans[index_without_it]
            return {'first_option': sentence + " " + sentences['first_option'].lower(), 'second_option': sentence + " " + sentences['second_option'].lower(), 'neutral': sentence + " " + sentences['neutral'].lower()}
    except:
        return "An error occurred translating sentence with it"       


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    sentence_fn = args["--sentence"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    translation = translate(sentence_fn)
    print(translation)

    logging.info("DONE")
