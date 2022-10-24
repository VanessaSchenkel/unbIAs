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
from spacy_utils import get_pronoun_on_sentence, get_pobj, get_only_subject_sentence,  get_people, get_nlp_en, display_with_pd, get_sentence_gender, get_nsubj_sentence, get_nlp_pt, has_gender_in_source, get_noun_chunks
from generate_model_translation import get_best_translation, generate_translation_with_constrained, generate_translation_with_gender_constrained, generate_translation, get_constrained_translation_one_subject, get_contrained_translation
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
        
    print("subjects, pronoun, gender", subjects, pronoun_list, gender)

    for token in source_sentence:
        print("---->", token, " | ", token.pos_, " | ", token.dep_, " | ", token.head)

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

def generate_translation_for_one_subj_neutral(source_sentence):
    # translation_nlp = get_nlp_pt("ele é um ótimo enfermeiro.")
    translation_nlp = get_google_translation(source_sentence.text_with_ws)        
    
    people = get_people(translation_nlp)
    constrained_splitted = test_constrained(translation_nlp, people)

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

    return translations       
            

def combine_contrained_translations(translations, constrained_splitted, source_sentence, matching_methods = "i", align = "itermax"):
    first_translation, second_translation = translations
    word_alignments = get_word_alignment_pairs(first_translation.strip("."), second_translation.strip("."), matching_methods=matching_methods, align=align)
    new_sentence = ""
    for first_sentence, second_sentence in word_alignments:
        last_word = new_sentence.strip().split(" ")[-1]

        if first_sentence == second_sentence and first_sentence != last_word:
            new_sentence += first_sentence + " "

        elif any(first_sentence in word for word in constrained_splitted) and first_sentence != last_word:
            new_sentence += first_sentence + " "
        
        elif any(second_sentence in word for word in constrained_splitted) and second_sentence != last_word:
            new_sentence += second_sentence + " "  
        
        elif first_sentence != second_sentence and first_sentence != last_word:
            first_token = get_nlp_pt(first_sentence)[0]
            second_token = get_nlp_pt(second_sentence)[0]

            if first_token.lemma_ == second_token.lemma_ or first_token.text[:-1] == second_token.text:
                new_sentence += first_sentence + " "
            
    
    if len(new_sentence.strip().split(' ')) < len(word_alignments):
        model_translation = get_best_translation(source_sentence.text_with_ws)
        model_alignment = get_word_alignment_pairs(model_translation.strip("."), new_sentence, matching_methods="m", align="mwmf")
        return align_with_model(model_alignment, new_sentence)
    

    return new_sentence.strip() + "."

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
            new_sentence_model += new_sentence.strip() + "."
            return new_sentence_model
    
    return new_sentence_model.strip() + "."



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
    list_constrained = []

    for token in translation:
        ancestors = [ancestor for ancestor in token.ancestors]
        children = [child for child in token.children]

        if not any(item in ancestors for item in people) and not any(item in children for item in people) and token not in people:
            if token.pos_ != "PUNCT" or len(constrained_sentence) > 0:
                constrained_sentence += token.text_with_ws
        
        elif token.text.lower() != 'eu' and len(constrained_sentence) > 0:
            list_constrained.append(constrained_sentence.strip())
            constrained_sentence = ""

        if token.is_sent_end and len(constrained_sentence) > 0:
            list_constrained.append(constrained_sentence.strip())
    
    if len(list_constrained) == 1 and len(translation.text_with_ws) == len(list_constrained[0]):
        return ""

    return list_constrained


    # TODO checar se o genero ta certo de quem she se refere (roberta ingles e roberta portugues?)
    # gerar as 3 traduções para quem deveria ser neutro   


# def get_google_translation(source_sentence):
#     if source_sentence.startswith("The") and source_sentence.endswith("designer"):
#         return get_nlp_pt("O desenvolvedor discutiu com o designer")
#     elif source_sentence.startswith("because") and source_sentence.endswith("design"):    
#         get_nlp_pt("porque ela não gostou do desenho.")
#     return get_nlp_pt("A desenvolvedora discutiu com a designer, porque ela não gostou do design.")

def is_all_equal(list):
    return all(i.text == list[0].text for i in list)

def is_neutral(pronoun_list):
    return len(pronoun_list) == 0 or all("I" == elem.text for elem in pronoun_list) or all("they" == elem.text for elem in pronoun_list)

def get_translation_for_one_word(source_sentence):
    try:
        translation = generate_translation(source_sentence)
        formatted =  translation.rstrip(".")

        formatted_translation = get_nlp_pt(formatted)
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

        # splitted_google_trans = split_sentence_same_subj(translation_google)
        # print("splitted_google_trans: ", splitted_google_trans)

        # splitted_source = split_sentence_same_subj(source_sentence)
        # print("splitted_source: ", splitted_source)

        # constrained_sentence = get_constrained(source_sentence)  
        # print("constrained_sentence: ", constrained_sentence)
        
        constrained_splitted = test_constrained(translation_google, [subject])
        
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

        # if len(constrained_sentence) == 0:
        #     print("ENTROU 1")
        #     best_translation = get_best_translation(source_sentence.text_with_ws)
        #     print("best_translation:", best_translation)
        #     neutral = make_neutral(best_translation)

        #     return str(translation_google), best_translation, neutral
        
        # elif len(splitted_google_trans) == 1:
        #     print("ENTROU 2")
        #     more_likely, less_likely = get_constrained_translation_one_subject(
        #         source_sentence, constrained_sentence)
        #     neutral = make_neutral_with_constrained(more_likely, constrained_sentence)
            
        #     return more_likely, less_likely, neutral
        # else:
        #     print("ENTROU 3")
        #     return generate_multiple_sentence_translation(splitted_google_trans, subject, splitted_source);
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
        sentences = format_sentence_inflections(possible_words)
    
        return sentences
    except:
        return "An error occurred translating sentence without pronoun and gender"    
 

def generate_translation_for_more_than_one_gender(source_sentence):
    try:
        sentences = format_sentence(source_sentence)
        translations_more_likely = []
        translations_neutral = []
        for sentence in sentences:
            
            should_remove_first = should_remove_first_word(sentence)
            
            sentence_to_translate = ""
            word_to_add = ""
            if should_remove_first:
                sentence_to_translate =  sentence.strip().split(' ', 1)[1]
                first_word = sentence.strip().split(' ', 1)[0]
                word_to_add = get_word_to_add(first_word) + " "
            else:
                sentence_to_translate = sentence
            
            sentence_to_translate += "."
            sent = get_nlp_en(sentence_to_translate)
            translations = generate_translation_for_one_subj(sent)
            more_likely = word_to_add + translations['more_likely']
            neutral = word_to_add + translations['neutral']
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
        # google_trans = get_google_translation(source_sentence.text_with_ws)
        google_trans = get_nlp_pt("O troféu não cabia na mala marrom porque era muito grande.")
        it_token = get_nlp_pt("it")
        subj_roberta = get_disambiguate_pronoun(source_sentence, it_token)
        print("SUBJ ROBERTA:", subj_roberta)

        google_trans = get_nlp_pt(google_trans)

        sentence_splitted_source = format_sentence(source_sentence)
        print("sentence_splitted_source:", sentence_splitted_source)

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
