"""Usage:
    generate_translations.py --sentence=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt
import more_itertools

# Local imports
from translation_google import get_google_translation, get_google_translation_word
from spacy_utils import get_people_source, get_pronoun_on_sentence, get_pobj, is_plural, get_only_subject_sentence, get_people, get_nlp_en, get_sentence_gender, get_nsubj_sentence, get_nlp_pt, has_gender_in_source, get_noun_chunks
from generate_model_translation import generate_translation_with_constrained, generate_translation_with_gender_constrained, generate_translation, get_constrained_translation_one_subject
from gender_inflection import get_just_possible_words, format_sentence_inflections
from constrained_beam_search import  get_constrained, get_constrained_translation, combine_contrained_translations, split_sentences_by_nsubj, split_on_subj_and_bsubj
from generate_neutral import make_neutral_with_constrained, make_neutral
from roberta import get_disambiguate_pronoun
from format_translations import format_sentence, format_multiple_sentence, format_sentence_more_than_one, format_with_dot, should_remove_first_word, format_translations_subjs, should_remove_last_word
from word_alignment import get_align_people, get_word_alignment_pairs

#The guard called the cleaner and asked her to open the door

def translate(source_sentence):
    if ' ' not in source_sentence.strip():
        return get_translation_for_one_word(source_sentence)

    source_sentence = get_nlp_en(source_sentence)
    subjects = get_nsubj_sentence(source_sentence)
    pronoun_list = get_pronoun_on_sentence(source_sentence)
    gender = get_sentence_gender(source_sentence)
    source_sentence = get_nlp_en(source_sentence)
    pobj_list = get_people_source(source_sentence)
        
    print("subjects, pronoun, gender, pobj_list", subjects, pronoun_list, gender, pobj_list)

    for token in source_sentence:
        print("---->", token, " | ", token.pos_, " | ", token.tag_, " | ", token.dep_, " | ", token.head , " | ", token.morph)

    is_all_same_pronoun = is_all_equal(pronoun_list)
    is_all_same_subject = is_all_equal(subjects)


    if is_all_same_pronoun and is_all_same_subject and len(pronoun_list) > 0 and len(pobj_list) <= len(pronoun_list):
        print("ENTROU 1")
        if is_neutral(pronoun_list):
            print("entrou neutro")
            return generate_translation_for_one_subj_neutral(source_sentence)

        return generate_translation_for_one_subj(source_sentence)
       
    elif len(gender) == 0 and len(set(pronoun_list)) == 0 and len(subjects) == 0:
        print("ENTROU 2")
        return generate_translation_for_sentence_without_pronoun_and_gender(source_sentence)

    elif len(gender) == 0 and len(set(pronoun_list)) == 0 and len(subjects) > 0:
        print("ENTROU 3")
        return generate_translation_with_subject_and_neutral(source_sentence)    

    ####### elif len(subjects) == len(set(pronoun_list)) and not is_all_same_subject:
    #     return generate_translation_for_more_than_one_gender(source_sentence)
        
    elif len(set(pronoun_list)) == 1 and all("it" == elem.text for elem in pronoun_list):
        print("ENTROU 4")
        return generate_translation_it(source_sentence)
    
    elif len(pobj_list) > len(pronoun_list):
        print("ENTROU 5")
        return generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence)

    elif len(subjects) == len(pronoun_list) and len(gender) > 1:
        print("ENTROU 6")
        return generate_translation_more_subjects(source_sentence, subjects)

    # else:
    #     #TODO ADD NEUTRAL
    #     google_trans = get_google_translation(source_sentence.text_with_ws)
    #     neutral = make_neutral(google_trans)
    #     return {"google_translation": google_trans, 'neutral': neutral}    



### METHODS
def is_all_equal(list):
    return all(i.text == list[0].text for i in list)

def is_neutral(pronoun_list):
    return len(pronoun_list) == 0 or all("I" == elem.text for elem in pronoun_list) or all("they" == elem.text.lower() for elem in pronoun_list)

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
    # translation_nlp = get_nlp_pt('O gerente se encontra com o conselheiro toda semana porque ele quer ter certeza de que tudo está de acordo com a lei')

    people = get_align_people(source_sentence, translation_nlp)

    print("PEOPLE:", people)
    constrained_splitted = split_on_subj_and_bsubj(translation_nlp, people)
    print("CONSTRAINED SPLITTED:", constrained_splitted)
    translations = []
    
    for constrained in constrained_splitted:
        constrained_translation = generate_translation_with_gender_constrained(source_sentence.text_with_ws, constrained)
        print("CONSTRAINED TRANSLATION:", constrained_translation)
        translation = check_constrained_translation(constrained, constrained_translation, source_sentence.text_with_ws)
        translations.append(translation)
    
    
    if len(translations) > 1:
        translation_constrained = combine_contrained_translations(translations, constrained_splitted, source_sentence)
    else:
        translation_constrained = translations[0]
    
    pronouns = get_pronoun_on_sentence(source_sentence)
    subjects = []
    for pronoun in pronouns:
        subject = get_disambiguate_pronoun(source_sentence, pronoun)
        subjects.append(subject)

    translations = get_gender_translations(subjects, source_sentence.text_with_ws, translation_constrained, people)

    return translations


def check_constrained_translation(constrained, constrained_translation, source_sentence):
    if len(constrained_translation) > (2*len(source_sentence)) and constrained_translation.endswith(constrained):
        translation = generate_translation(source_sentence)
        return translation
    else:
        return constrained_translation   

def get_gender_translations(subjects, source_sentence, translation_constrained, people):
        # word_alignments = get_word_alignment_pairs(source_sentence, translation_constrained, matching_methods="m", align="mwmf")
        # subj_translated = []

        # print("###############################")
        # print("subjects:", subjects)

        # for subject in subjects:      
        #     print("subject:", subject)      
        #     for first_sentence, second_sentence in word_alignments:
        #         print(first_sentence,  " ===> ", second_sentence)
        #         if first_sentence in subject:
        #             subj_translated.append(second_sentence)
        #         elif second_sentence in subject:
        #             subj_translated.append(first_sentence)
        
        # print("subj_translated", subj_translated)
        # people_to_neutral = []
        # for person in people:
        #     if person.text not in subj_translated:
        #         if person.text.endswith('s'):
        #             people_to_neutral.append(person.text[:-2])
        #         else:
        #             people_to_neutral.append(person.text[:-1])    

        
        # print("people_to_neutral", people_to_neutral)

        people_to_neutral = []
        source = get_nlp_en(source_sentence)
        source_people = get_people_source(source)
        print("source_people", source_people)

        p = [person.split()[-1] for person in subjects]
        print("p:", p)

        for person in source_people:
            print("person", person)
            print(person.text not in p)
            if person.text not in p:
                person_translated = generate_translation(person.text_with_ws)
                print("person translation", person_translated)
                people_to_neutral.append(person_translated.lower().strip(".")[:-1])


        print("people_to_neutral", people_to_neutral)
        words_to_neutral = []
        translation = get_nlp_pt(translation_constrained)
        index_to_replace = []

        for index, token in enumerate(translation):
            print(token.text[:-1] in people_to_neutral, token.head.text[:-1] in people_to_neutral)
            if token.head.text[:-1] in people_to_neutral or token.text[:-1] in people_to_neutral:
                words_to_neutral.append(token)
                index_to_replace.append(index)

        print("WORDS TO NATURAL", words_to_neutral)        

        inflections = get_just_possible_words(words_to_neutral)
        first_sentence, second_sentence, third_sentence = format_translations_subjs(index_to_replace, translation, inflections)
        
        return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence} 
   

def get_translation_for_one_word(source_sentence):
    try:
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
    except:
        return "An error occurred translating one word"

def generate_translation_for_one_subj(source_sentence):
    try:
        translation_google =  get_google_translation(source_sentence.text_with_ws) 
        # translation_google =  get_nlp_pt("Ela é uma boa médica.") 
        subject = get_only_subject_sentence(translation_google)
        if subject.pos_ == 'NOUN':
            constrained_sentence = get_constrained(source_sentence) 
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
        return {"error": "An error occurred translating for one subject"}


def generate_translation_with_subject_and_neutral(source_sentence):
    try:
        translation = generate_translation(source_sentence.text, 2)
        translation_nlp = get_nlp_pt(translation[0])
        neutral = make_neutral(translation_nlp)

        return {"first_option": translation[0], "second_option": translation[1], "neutral": neutral}
    except:
        return {"error": "An error occurred translating for one subject without pronoun"}   
 
def generate_neutral_translation(translation):
    try:
        possible_words = get_just_possible_words(translation)
        first_option, second_option, neutral = format_sentence_inflections(possible_words)
    
        return {"first_option": first_option, "second_option": second_option, "neutral": neutral}
    except:
        return {"error": "An error occurred translating sentence with they"}

def generate_translation_for_sentence_without_pronoun_and_gender(source_sentence):
    try:
        translation = generate_translation(source_sentence.text_with_ws)
        translation = get_nlp_pt(translation)
        possible_words = get_just_possible_words(translation)
        first_option, second_option, neutral = format_sentence_inflections(possible_words)
        
        return {"first_option": first_option, "second_option": second_option, "neutral": neutral}
    except:
        return {"error": "An error occurred translating sentence without pronoun and gender"}     
 

def generate_translation_for_more_than_one_gender(source_sentence):
    try:
        sentences = format_sentence_more_than_one(source_sentence)
        translations_more_likely = []
        translations_neutral = []

        for sentence in sentences:
            should_remove_first = should_remove_first_word(sentence)
            should_remove_last = should_remove_last_word(sentence[-1])
            sentence_to_translate = ""
            word_to_add = ""
            word_to_add_last = ""
            if should_remove_first:
                sentence_to_translate =  sentence.strip().split(' ', 1)[1]
                first_word = sentence.strip().split(' ', 1)[0]
                word_to_add = get_word_to_add(first_word) + " "
            elif should_remove_last:
                sentence_to_translate =  sentence.strip()[:-1]
                last_word = sentence.strip().split(' ', 1)[-1]
                word_to_add_last = get_word_to_add(last_word)
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
        return {"error": "An error occurred translating more than one gender on the sentence"}     

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

        translations_more_likely = []
        translations_neutral = []

        for sentence in collapsed:
            should_remove_first = should_remove_first_word(sentence)
            should_remove_last = should_remove_last_word(sentence[-1])
            sentence_to_translate = ""
            word_to_add = ""
            word_to_add_last = ""
            if should_remove_first:
                sentence_to_translate =  sentence.strip().split(' ', 1)[1]
                first_word = sentence.strip().split(' ', 1)[0]
                word_to_add = get_word_to_add(first_word) + " "
            elif should_remove_last:
                sentence_to_translate =  sentence.strip()[:-1]
                last_word = sentence.strip().split(' ', 1)[-1]
                word_to_add_last = get_word_to_add(last_word)
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

        return {'translation': sentence_more_likely, 'neutral': sentence_neutral}
    except:
        return {"error": "An error occurred translating more than one subject"}         

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
        return {"error": "An error occurred translating sentence with it"}         


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
