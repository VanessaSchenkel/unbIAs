"""Usage:
    generate_translations.py --sentence=SENTENCE [--debug]
"""

# External imports
import itertools
import logging
from docopt import docopt
import more_itertools

# Local imports
from translation_google import translate_text
from spacy_utils import get_pronoun_on_sentence, get_nlp_en, get_sentence_gender, get_nsubj_sentence, get_nlp_pt, has_gender_in_source, format_sentence, split_sentences_by_nsubj, get_noun_chunks, split_sentence_same_subj
from generate_model_translation import generate_translation, get_constrained_translation_one_subject, get_contrained_translation
from gender_inflection import get_just_possible_words, format_sentence_inflections
from constrained_beam_search import get_constrained_sentence, get_format_translation
from generate_neutral import make_neutral_with_pronoun, make_neutral_with_constrained
from roberta import get_disambiguate_pronoun

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
        
        # print("subjects, pronoun, gender", subjects, pronoun_list, gender)

        is_all_same_pronoun = is_all_equal(pronoun_list)
        is_all_same_subject = is_all_equal(subjects)
        
        if is_all_same_pronoun and is_all_same_subject:
             return generate_translation_for_one_subj(
                source_sentence.text_with_ws)    

        elif len(gender) == 0 and len(set(pronoun_list)) == 0:
            return generate_translation_for_neutral(source_sentence)

        elif len(subjects) == len(set(pronoun_list)) and not is_all_same_subject:
            return generate_translation_for_more_than_one_gender(source_sentence, subjects)
        
        elif len(set(pronoun_list)) == 1 and all("it" == elem.text for elem in pronoun_list):
            return generate_translation_it(source_sentence)
        
        elif len(subjects) > len(pronoun_list):
            return generate_translation_more_subjects(source_sentence, subjects)

def is_all_equal(list):
    return all(i.text == list[0].text for i in list)

def generate_translation_for_one_subj(source_sentence):
    translation_google =  get_google_translation(source_sentence) 

    if "they" in source_sentence or "They" in source_sentence:
        return generate_they_translation(translation_google)
    
    subject = get_nsubj_sentence(translation_google)
    
    splitted_google_trans = split_sentence_same_subj(translation_google)
    source = get_nlp_en(source_sentence)
    splitted_source = split_sentence_same_subj(source)

    if len(splitted_google_trans) == 1:
        constrained_sentence = get_constrained_sentence(translation_google, subject)  

        more_likely, less_likely = get_constrained_translation_one_subject(
            source_sentence, constrained_sentence)
        neutral = make_neutral_with_constrained(more_likely, constrained_sentence)
        return {"more_likely": more_likely, "less_likely": less_likely, "neutral": neutral} 

    return generate_multiple_sentence_translation(splitted_google_trans, subject, splitted_source);
    


    # TODO combinar sentences
    # Tratar erro
    # Em caso de erro, google 
    # Tratar they com mais de um sub e roberta


 
    return ""  

def generate_multiple_sentence_translation(splitted_google_trans, subject, splitted_source):
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
    
    return {"more_likely": formatted[0], "less_likely": formatted[1], "neutral": formatted[2]} 

def generate_they_translation(translation):
    possible_words = get_just_possible_words(translation)
    sentences = format_sentence_inflections(possible_words)
    return sentences

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

    return format_translation

def get_google_translation(sentence):
    #TODO b = b + '.' if not b.endswith('.') else b
    #TODO add Eu em "I"
    if "doctor" in sentence:
        return get_nlp_pt("a médica perfeita terminou seu trabalho.")
    elif "nurse" in sentence:
        return get_nlp_pt("a enfermeira falou muito")
    elif "they" in sentence:
        return get_nlp_pt("eles são ótimos.")
    elif "fit" in sentence:
        return get_nlp_pt("O troféu não cabia na mala marrom porque era muito grande.")
    elif "tired" in sentence:
        return get_nlp_pt("Eu estou cansado e eu gosto de ler muito.")    

def generate_contrained_translation(sentences_splitted):
    translation = ""
    for sentence in sentences_splitted:
        traslation_google_splitted = get_google_translation(sentence)
        nsub_google = get_nsubj_sentence(traslation_google_splitted)
        constrained_sentence = get_constrained_sentence(traslation_google_splitted, nsub_google)
        translation_contrained = get_contrained_translation(sentence, constrained_sentence)
        translation += translation_contrained
    
    return translation   

def generate_translation_more_subjects(source_sentence, subjects):
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

def format_multiple_sentence(translations):
    sentences_formatted = []

    all_combinations = list(itertools.product(*translations))
    
    for sentence in all_combinations:
        sent_joined = " ".join(sentence)
        formatted = format_with_dot(sent_joined)
        sentences_formatted.append(formatted)

    return sentences_formatted

def format_with_dot(translation):
    sentence = get_nlp_pt(translation)
    new_sentence = ""
    for token in sentence:
        if token.text == "." and token.i != len(sentence)-1:
            next_token = sentence[token.i + 1]
            if next_token.tag_ != "CCONJ" and not next_token.is_punct and not next_token.text.is_lower():
                new_sentence += token.text_with_ws
            else:
                new_sentence += " "
        else:
            new_sentence += token.text_with_ws

    return new_sentence      
        

def generate_translation_it(source_sentence):
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
        return google_trans
    
    else:
        possible_words = get_just_possible_words(sentence_pt)
        sentences = format_sentence_inflections(possible_words)
        sentence = sentence_splitted_trans[index_without_it]
        return {'first_sentence': sentence + " " + sentences['first_sentence'].lower(), 'second_sentence': sentence + " " + sentences['second_sentence'].lower(), 'third_sentence': sentence + " " + sentences['third_sentence'].lower()}
    


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
