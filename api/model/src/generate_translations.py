"""Usage:
    generate_translations.py --sentence=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt
import more_itertools
import re

# Local imports
from translation_google import get_google_translation
from spacy_utils import get_pronoun_on_sentence, get_pobj, get_people, get_nlp_en, display_with_pd, get_sentence_gender, get_nsubj_sentence, get_nlp_pt, has_gender_in_source, get_noun_chunks
from generate_model_translation import get_best_translation, generate_translation_with_gender_constrained, generate_translation, get_constrained_translation_one_subject, get_contrained_translation
from gender_inflection import get_just_possible_words, format_sentence_inflections
from constrained_beam_search import get_constrained_sentence, split_sentences_by_nsubj, split_sentence_same_subj, get_constrained, get_constrained_gender
from generate_neutral import make_neutral_with_pronoun, make_neutral_with_constrained, make_neutral
from roberta import get_disambiguate_pronoun
from format_translations import format_sentence, get_format_translation, format_multiple_sentence, should_remove_first_word, format_with_dot
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
        first_sentence, second_sentence, third_sentence =  generate_translation_for_one_subj(source_sentence.text_with_ws)
       
        if is_neutral(pronoun_list):
            return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence}
        
        return {"more_likely": first_sentence, "less_likely": second_sentence, "neutral": third_sentence}
    
    elif len(gender) == 0 and len(set(pronoun_list)) == 0 and len(subjects) == 0:
        return generate_translation_for_sentence_without_pronoun_and_gender(source_sentence)

    elif len(gender) == 0 and len(set(pronoun_list)) == 0 and len(subjects) > 0:
        return generate_translation_with_subject_and_neutral(source_sentence)    

    elif len(subjects) == len(set(pronoun_list)) and not is_all_same_subject:
        return generate_translation_for_more_than_one_gender(source_sentence, subjects)
        
    elif len(set(pronoun_list)) == 1 and all("it" == elem.text for elem in pronoun_list):
        return generate_translation_it(source_sentence)
    
    elif len(subjects) > len(pronoun_list) and len(pobj_list) > 0:
        return generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence)

    elif len(subjects) > len(pronoun_list):
        return generate_translation_more_subjects(source_sentence, subjects)

    else:
        google_trans = get_google_translation(source_sentence)
        return {"google_translation": google_trans}    

        
def generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence):
    print("AQUI CARALHO")
    translation_nlp = get_nlp_pt("A desenvolvedora discutiu com a designer porque ela não gostou do design.")
    people = get_people(translation_nlp)
    constrained_splitted = split_on_subj_and_bsubj(translation_nlp, people)
    translations = []
    for constrained in constrained_splitted:
        constrained_translation = generate_translation_with_gender_constrained(source_sentence.text_with_ws, constrained)
        translations.append(constrained_translation)
    
    translation_constrained = combine_contrained_translations(translations, constrained_splitted, source_sentence)
    
    # pronouns = get_pronoun_on_sentence(source_sentence)

    # subjects = []
    # for pronoun in pronouns:
    #     subject = get_disambiguate_pronoun(source_sentence, pronoun)
    #     subjects.append(subject)

    # print("----")
    # print(pronouns)
    # print(subjects) 

    subjects = [{'pronoun': 'she', 'subject':'The developer'}]
    get_gender_translations(subjects, source_sentence.text_with_ws, translation_constrained, people)


    return ""
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
        
        print("gender pronoun:", gender_pronoun)  

        translation_subj = get_nlp_pt(subj_translated)
        translation_gender = set(get_sentence_gender(translation_subj))
        
        print("translation_gender:", translation_gender)

        people_to_neutral = [person.text for person in people if person.text not in subj_translated]
        
        words_to_neutral = []
        translation = get_nlp_pt(translation_constrained)
        index_to_replace = []

        for index, token in enumerate(translation):
            if token.head.text in people_to_neutral or token.text in people_to_neutral:
                words_to_neutral.append(token)
                index_to_replace.append(index)

        print("------")
        print(words_to_neutral)
        inflections = get_just_possible_words(words_to_neutral)
        print(inflections)
        print(index_to_replace)

        first_sentence, second_sentence, third_sentence = format_translations_subjs(index_to_replace, translation, inflections)
        
        return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence}

        
def format_translations_subjs(index_to_replace, sentence, inflections):
    translations = []
    for id, index in enumerate(index_to_replace):
        new_sentence = ""
        cont = 0
        for index, word in enumerate(sentence):
            if index not in index_to_replace:
                new_sentence += word.text + " "
            else:
                new_sentence += inflections[cont][id] + " "
                cont = cont + 1
        
        translations.append(new_sentence.strip())

    print("TRANSLATIONS ---->", translations)
    return translations       
            

def combine_contrained_translations(translations, constrained_splitted, source_sentence):
    first_translation, second_translation = translations
    word_alignments = get_word_alignment_pairs(first_translation, second_translation)
    new_sentence = ""
    for first_sentence, second_sentence in word_alignments:
        last_word = new_sentence.strip().split(" ")[-1]
        if first_sentence == second_sentence and first_sentence != last_word:
            new_sentence += first_sentence + " "
        elif any(first_sentence in word for word in constrained_splitted) and first_sentence != last_word:
            new_sentence += first_sentence + " "
        elif any(second_sentence in word for word in constrained_splitted) and second_sentence != last_word:
            new_sentence += second_sentence + " "

    if len(new_sentence.split(' ')) < len(word_alignments):
        model_translation = get_best_translation(source_sentence.text_with_ws)
        model_alignment = get_word_alignment_pairs(model_translation, new_sentence, matching_methods="m", align="mwmf")
        return align_with_model(model_alignment, new_sentence)
    
    return new_sentence.strip()

def align_with_model(model_alignment, new_sentence):
    new_sentence_model = ""
    for model_sentence, alignment_sentence in model_alignment:
        last_word = new_sentence_model.strip().split(" ")[-1]
        if model_sentence != alignment_sentence and model_sentence != last_word:
            token_model = get_nlp_pt(model_sentence)[0]
            token_alignment = get_nlp_pt(alignment_sentence)[0]
            
            if token_model.pos_ != token_alignment.pos_:
                new_sentence_model += model_sentence + " "
            
  
        if model_sentence == alignment_sentence:
            new_sentence_model += new_sentence
            return new_sentence_model.strip()

    return new_sentence_model.strip() 



def split_on_subj_and_bsubj(sentence, people):
    sentence_splitted = []
    new_sent = ""   
    
    for token in sentence:
        if token not in people and token.pos_ != "DET":
            new_sent += token.text_with_ws
        elif token.pos_ == "DET" and token.head not in people:
            new_sent += token.text_with_ws
             
        if token.is_sent_end or token in people:
            if len(new_sent) > 0:
                sentence_splitted.append(new_sent.strip())

            new_sent = ""
                       
    return sentence_splitted      


def test_constrained(translation, people):
    constrained_sentence = ""

    for token in translation:
        ancestors = [ancestor for ancestor in token.ancestors]
        children = [child for child in token.children]

        if not any(item in ancestors for item in people) and not any(item in children for item in people) and token not in people:
            constrained_sentence += token.text_with_ws

    return constrained_sentence


    # TODO checar se o genero ta certo de quem she se refere (roberta ingles e roberta portugues?)
    # gerar as 3 traduções para quem deveria ser neutro   


def get_google_translation(source_sentence):
    if source_sentence.startswith("The") and source_sentence.endswith("designer"):
        return get_nlp_pt("O desenvolvedor discutiu com o designer")
    elif source_sentence.startswith("because") and source_sentence.endswith("design"):    
        get_nlp_pt("porque ela não gostou do desenho.")
    return get_nlp_pt("A desenvolvedora discutiu com a designer, porque ela não gostou do design.")

def is_all_equal(list):
    return all(i.text == list[0].text for i in list)

def is_neutral(pronoun_list):
    return len(pronoun_list) == 0 or all("I" == elem.text for elem in pronoun_list) or all("they" == elem.text for elem in pronoun_list)

def get_translation_for_one_word(source_sentence):
    try:
        translation = generate_translation(source_sentence)
        print(translation, "translation")
        formatted =  translation.rstrip(".")

        formatted_translation = get_nlp_pt(formatted)
        possible_words = get_just_possible_words(formatted_translation)[0]
        possible_words_formatted = [word.capitalize() for word in possible_words]
        return {'possible_words': possible_words_formatted}    
    except:
        return "An error occurred translating one word"

def generate_translation_for_one_subj(source_sentence):
    try:
        translation_google =  get_google_translation(source_sentence) 
        print("translation_google ===", translation_google)
        
        if "they" in source_sentence or "They" in source_sentence:
            return generate_they_translation(translation_google)
        
        subject = get_nsubj_sentence(translation_google)
        print("subject ===", subject)
        splitted_google_trans = split_sentence_same_subj(translation_google)
        print("splitted_google_trans ===", splitted_google_trans)
        source = get_nlp_en(source_sentence)
        
        splitted_source = split_sentence_same_subj(source)
        print("splitted_source ===", splitted_source)

        constrained_sentence = get_constrained(source_sentence)  
        print("constrained_sentence ===", constrained_sentence)   

        if len(constrained_sentence) == 0:
            print("ENTROU 1")
            best_translation = get_best_translation(source_sentence)
            neutral = make_neutral(best_translation)

            return str(translation_google), best_translation, neutral
        
        elif len(splitted_google_trans) == 1:
            print("ENTROU 2")
            more_likely, less_likely = get_constrained_translation_one_subject(
                source_sentence, constrained_sentence)
            neutral = make_neutral_with_constrained(more_likely, constrained_sentence)
            
            return more_likely, less_likely, neutral
        else:
            print("ENTROU 3")
            return generate_multiple_sentence_translation(splitted_google_trans, subject, splitted_source);
    except:
        return "An error occurred translating for one subject"

    # Tratar they com mais de um sub e roberta

def generate_translation_with_subject_and_neutral(source_sentence):
    try:
        translation = generate_translation(source_sentence.text, 2)
        translation_nlp = get_nlp_pt(translation[0])
        neutral = make_neutral(translation_nlp)

        return {"first_option": translation[0], "second_option": translation[1], "neutral": neutral}
    except:
        return "An error occurred translating for one subject without pronoun"  

def generate_multiple_sentence_translation(splitted_google_trans, subject, splitted_source):
    try:
        possible_sentences = []
        for index, sentence in enumerate(splitted_google_trans):
            sentence_translated = get_nlp_pt(sentence)
            gender = get_sentence_gender(sentence_translated)

            if len(gender) > 0:
                constrained_sentence = get_constrained_sentence(sentence_translated, subject)  
                more_likely, less_likely = get_constrained_translation_one_subject(splitted_source[index], constrained_sentence)
                neutral = make_neutral_with_pronoun(more_likely)
                possible_sentences.append([more_likely, less_likely, neutral])
            else:
                possible_sentences.append([sentence])

        
        formatted = format_multiple_sentence(possible_sentences)         

        return formatted[0], formatted[1], formatted[2] 
    except:
        return "An error occurred translating multiple sentence"    

def generate_they_translation(translation):
    try:
        possible_words = get_just_possible_words(translation)
        first_option, second_option, neutral = format_sentence_inflections(possible_words)
    
        return first_option, second_option, neutral
    except:
        return "An error occurred translating sentence with they"    

def generate_translation_for_sentence_without_pronoun_and_gender(source_sentence):
    try:
        translation = generate_translation(source_sentence.text)
        translation = get_nlp_pt(translation)
        possible_words = get_just_possible_words(translation)
        sentences = format_sentence_inflections(possible_words)
    
        return sentences
    except:
        return "An error occurred translating sentence without pronoun and gender"    

def generate_translation_for_more_than_one_gender(source_sentence, subjects):
    try:
        sentence = format_sentence(source_sentence)
        splitted_list = []
        
        for sent in sentence:
            sent = get_nlp_en(sent)
            splitted_list.append(split_sentences_by_nsubj(sent, subjects))
        
        collapsed = list(more_itertools.collapse(splitted_list))

        translation = generate_contrained_translation(collapsed)
        format_translation = format_with_dot(translation)

        return format_translation
    except:
        return "An error occurred translating more than one gender on the sentence"    


def generate_contrained_translation(sentences_splitted):
    try:
        translation = ""
        for sentence in sentences_splitted:
            translation_google_splitted = get_google_translation(sentence)
            constrained_sentence = get_constrained_gender(translation_google_splitted)
            
            should_remove_first = should_remove_first_word(sentence)
            
            sentence_to_translate = ""
            word_to_add = ""
            if should_remove_first:
                sentence_to_translate =  sentence.split(' ', 1)[1]
                word_to_add = " " + translation_google_splitted.text_with_ws.split()[0] + " "
            else:
                sentence_to_translate = sentence
    
            translation_contrained = generate_translation_with_gender_constrained(sentence_to_translate, constrained_sentence)
            translation = translation + word_to_add + translation_contrained

        return translation   
    except:
        return "An error occurred generating constrained translation"       

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
        google_trans = "O troféu não cabia na mala marrom porque era muito grande."
        subj_roberta = get_disambiguate_pronoun(source_sentence, "it")
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
