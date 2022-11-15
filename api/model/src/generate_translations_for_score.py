"""Usage:
    generate_translations_for_score.py --sent=SENTENCE --trans=TRANS [--debug]
"""
# External imports
import logging
from docopt import docopt
import more_itertools
from split_sentence import split_on_subj_and_bsubj, split_sentences_by_nsubj

# Local imports
from spacy_utils import  get_morph, get_people_source, get_pronoun_on_sentence, get_pronoun_on_sentence_with_it, get_translation_with_punctuation, get_words_to_neutral_and_index_to_replace, is_plural, get_only_subject_sentence, get_people, get_nlp_en, get_sentence_gender, get_nsubj_sentence, get_nlp_pt, get_noun_chunks
from generate_model_translation import generate_translation_with_constrained, generate_translation, generate_translation_with_gender_constrained
from gender_inflection import  get_just_possible_words, format_sentence_inflections
from constrained_beam_search import  check_constrained_translation, combine_translations, generate_constrain_subject_and_neutral, get_constrained_one_subj, get_constrained_translation, combine_contrained_translations, get_constrained_without_people,  get_translations_aligned, get_translations_with_constrained, get_word_to_add
from generate_neutral import make_neutral_with_constrained, make_neutral
from roberta import get_disambiguate_pronoun, get_subject_source
from format_translations import format_question, format_sentence, format_translations_subjs, should_remove_first_word, should_remove_last_word
from word_alignment import get_align_people, get_people_model, get_people_to_neutral_and_people_google, get_subject_translated_aligned, get_translations_aligned_model_google, get_word_alignment_pairs

def generate_translations_for_score(source_sentence, google_translation):
    try:
        if ' ' not in source_sentence.text.strip():
            return get_translation_for_one_word(source_sentence.text, google_translation.text)

        subjects = get_nsubj_sentence(source_sentence)
        pronoun_list = get_pronoun_on_sentence(source_sentence)
        pronoun_list_it = get_pronoun_on_sentence_with_it(source_sentence)
        gender = get_sentence_gender(source_sentence)
        people_source = get_people_source(source_sentence)
            
        is_all_same_pronoun = is_all_equal(pronoun_list)
        is_all_same_subject = is_all_equal(subjects)
        
        # print("subjects: ", subjects,  "pronoun_list ", pronoun_list, "pronoun_list_it: ", pronoun_list_it, "gender: ", gender, "people_source: ", people_source)

        # for token in source_sentence:
        #     print("---->", token, " | ", token.pos_, " | ", token.tag_, " | ", token.dep_, " | ", token.head , " | ", token.morph)

        if is_all_same_pronoun and is_all_same_subject and len(pronoun_list_it) > 0 and len(subjects) > 0 and len(people_source) <= len(pronoun_list_it) and len(people_source) > 0:
            print("-------> ENTROU 1")
            if is_neutral(pronoun_list, gender):
                print("entrou neutro")
                return generate_translation_for_one_subj_neutral(source_sentence, google_translation)

            return generate_translation_for_one_subj(source_sentence, google_translation)
        
        elif len(gender) == 0 and len(set(pronoun_list)) == 0 and len(subjects) == 0:
            print("-------> ENTROU 2")
            return generate_translation_for_sentence_without_pronoun_and_gender(source_sentence, google_translation)

        elif (len(gender) == 0 and len(set(pronoun_list)) == 0 and len(subjects) > 0) or (len(gender) == 1 and len(pronoun_list) == 1 and len(people_source) == 0):
            print("-------> ENTROU 3")
            return generate_translation_with_subject_and_neutral(source_sentence, google_translation)    
            
        elif len(set(pronoun_list)) == 1 and all("it" == elem.text for elem in pronoun_list_it):
            print("-------> ENTROU 4")
            return generate_translation_it(source_sentence, google_translation)
        
        elif len(pronoun_list) > 0 and (len(people_source) > len(pronoun_list) or len(people_source) > len(gender) or (len(gender) > 1 and 'Neut' in gender)):
            print("-------> ENTROU 5")
            return generate_translation_for_poj(source_sentence, google_translation)
            # return generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence, google_translation)

        elif len(subjects) == len(pronoun_list) and len(subjects) > 0 and len(gender) > 1:
            print("-------> ENTROU 6")
            return generate_translation_more_subjects(source_sentence, subjects, google_translation, people_source)
        
        elif len(subjects) > len(pronoun_list) and (len(people_source) == 0 or len(pronoun_list_it) == 0):
            print("-------> ENTROU 7")
            return generate_translation_without_people(source_sentence,  google_translation)
        else:
            print("-------> ENTROU ELSE")
            return generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence, google_translation)  
    
    except:        
        model_translation = generate_translation(source_sentence.text_with_ws)
        model_nlp = get_nlp_pt(model_translation)
        first_option, second_option, neutral =  generate_neutral_translation(model_nlp)
        return {"first_option": first_option, 'second_option': second_option, 'neutral': neutral}     


def is_all_equal(list: list):
    return all(i.text == list[0].text for i in list)


def is_neutral(pronoun_list: list, gender):
    return ['Neut'] == gender or len(gender) == 0  or len(pronoun_list) == 0 or all("I" == elem.text for elem in pronoun_list) or all("they" == elem.text.lower() for elem in pronoun_list) or all("we" == elem.text.lower() for elem in pronoun_list)


def get_translation_for_one_word(source_sentence: str, google_translation):
        translation = generate_translation(source_sentence)
        formatted =  translation.rstrip(".")
        formatted_translation = get_nlp_pt(formatted)
        source = get_nlp_en(source_sentence)
        is_source_plural = is_plural(source)
        is_translation_plural = is_plural(formatted_translation)

        if is_source_plural != is_translation_plural:
            formatted_translation = google_translation
        
        possible_words = get_just_possible_words(formatted_translation)[0]
        possible_words_formatted = [word.capitalize() for word in possible_words]

        return {'possible_words': possible_words_formatted}    


def generate_translation_for_one_subj_neutral(source_sentence, google_translation):
        translation_nlp = google_translation   
        
        people = get_people(translation_nlp)
        constrained_splitted = get_constrained_translation(translation_nlp, people)

        if len(constrained_splitted) == 0:
            return generate_neutral_translation(translation_nlp)

        translations = []
        for constrained in constrained_splitted:
            constrained_translation = generate_translation_with_constrained(source_sentence.text_with_ws, constrained)
            translations.append(constrained_translation)

        translation = get_translations_aligned(translations, constrained_splitted, source_sentence)

        translation_formatted = get_translation_with_punctuation(translation_formatted.text)
        possible_words = get_just_possible_words(translation)
        first_sentence, second_sentence, third_sentence = format_sentence_inflections(possible_words)
        
        return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence}   


def generate_translation_for_one_subj(source_sentence, google_translation):
        translation_google =  google_translation
        subject = get_only_subject_sentence(translation_google)
        
        constrained_splitted = get_constrained_one_subj(translation_google, [subject])
        if len(constrained_splitted) == 0:
            constrained_splitted = get_constrained_without_people(google_translation)

        translations = []
        for constrained in constrained_splitted:
            constrained_translation = generate_translation_with_constrained(source_sentence.text_with_ws, constrained)
            translations.append(constrained_translation)
        
        translation = get_translations_aligned(translations, constrained_splitted, source_sentence)
        possible_words = get_just_possible_words(translation)
        first_sentence, second_sentence, third_sentence = format_sentence_inflections(possible_words)
        
        return {"translation": first_sentence, "neutral": third_sentence}



def generate_translation_for_sentence_without_pronoun_and_gender(source_sentence, google_translation):
        translation = generate_translation(source_sentence.text_with_ws)
        translation_nlp = get_translation_with_punctuation(translation)
        
        possible_words = get_just_possible_words(translation_nlp)
        first_option, second_option, neutral = format_sentence_inflections(possible_words)
        
        return {"first_option": first_option, "second_option": second_option, "neutral": neutral}


def generate_translation_with_subject_and_neutral(source_sentence, google_translation):
        source = format_question(source_sentence.text)
        translation_model = generate_translation(source)
        constrained = generate_constrain_subject_and_neutral(google_translation)
        
        translation = get_translations_aligned_model_google(google_translation, translation_model, constrained)        
        possible_words = get_just_possible_words(translation)
        first_option, second_option, neutral = format_sentence_inflections(possible_words)
        
        return {"first_option": first_option, "second_option": second_option, "neutral": neutral}


def generate_translation_it(source_sentence, google_translation):
        google_trans = google_translation
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
            return  google_trans.replace(".", "").strip() + "."
    
        else:
            possible_words = get_just_possible_words(sentence_pt)
            sentences = format_sentence_inflections(possible_words)
            sentence = sentence_splitted_trans[index_without_it]
            first_option = sentence + " " + sentences['first_option'].lower().replace(".", "").strip() + "."
            return first_option
    
    
def generate_translation_for_nsubj_and_pobj_with_pronoun(source_sentence, translation_google):
    translation_nlp = translation_google
    people = get_align_people(source_sentence, translation_nlp)
    
    translation_model = generate_translation(source_sentence)    
    translation_model_nlp = get_nlp_pt(translation_model)
    
    subject_source = get_subject_source(source_sentence)
    source_people = get_people_source(source_sentence)
    people_model = get_people_model(source_sentence, translation_model_nlp, subject_source)
    
    people_to_neutral_source = [person.text for person in source_people if person.text != subject_source]
    
    people_to_neutral, people_google = get_people_to_neutral_and_people_google(source_sentence, translation_nlp, people_to_neutral_source, subject_source)
    
    people_model_nlp = get_nlp_pt(people_model)
    people_google_nlp = get_nlp_pt(people_google)
    model_morph = get_morph(people_model_nlp)
    model_google = get_morph(people_google_nlp)
    
    gender_people_model = get_sentence_gender(people_model_nlp)

    if (people_google == None or len(people_google) == 0) and len(people_model_nlp) > 0:
        translation_nlp = translation_model_nlp
    elif len(gender_people_model) > 0 and model_morph != model_google: 
        constrained_splitted = split_on_subj_and_bsubj(translation_nlp, people)
        translations = get_translations_with_constrained(source_sentence, constrained_splitted)    
        translations_aligned_model = get_translations_aligned(translations, constrained_splitted, source_sentence)
        subj_translated = get_subject_translated_aligned(source_sentence, translations_aligned_model, subject_source)
        translation_nlp = get_translations_aligned_model_google(translation_nlp, translations_aligned_model, subj_translated)
    elif people_model == people_google:
        translation_nlp = combine_translations(translation_nlp, people_google, translation_model_nlp, people_model)
    
    words_to_neutral, index_to_replace = get_words_to_neutral_and_index_to_replace(translation_nlp, people_to_neutral)
    inflections = get_just_possible_words(words_to_neutral)
    first_sentence, second_sentence, third_sentence = format_translations_subjs(index_to_replace, translation_nlp, inflections)
    
    return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence}

def generate_translation_without_people(source_sentence,  google_translation):
    constrained_splitted = get_constrained_without_people(google_translation)
    
    translations = []
    for constrained in constrained_splitted:
        constrained_translation = generate_translation_with_constrained(source_sentence.text_with_ws, constrained)
        translations.append(constrained_translation)
    
    translations_aligned_model = get_translations_aligned(translations, constrained_splitted, source_sentence)

    translation_nlp = get_translation_with_punctuation(translations_aligned_model.text)

    possible_words = get_just_possible_words(translation_nlp)
    first_sentence, second_sentence, third_sentence = format_sentence_inflections(possible_words)
    
    return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence}
 
def generate_translation_more_subjects(source_sentence, subjects, google_translation, people):
        sentence = format_sentence(source_sentence)
        
        if len(people) == 0:
            translation = generate_translation(source_sentence)
            translation_nlp = get_nlp_pt(translation)
            possible_words = get_just_possible_words(translation_nlp)
            first_sentence, second_sentence, third_sentence = format_sentence_inflections(possible_words)
    
            return {"first_option": first_sentence, "second_option": second_sentence, "neutral": third_sentence}
        
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
            
            sent = get_nlp_en(sentence_to_translate)
            translations = generate_translation_for_one_subj(sent, google_translation)
            more_likely = word_to_add + translations + word_to_add_last
            neutral = word_to_add + translations['neutral'] + word_to_add_last
            translations_more_likely.append(more_likely)
            translations_neutral.append(neutral)

        sentence_more_likely = " ".join(translations_more_likely).replace(".", "").lower().capitalize() + "."
        sentence_neutral = " ".join(translations_neutral).replace(".", "").lower().capitalize() + "."

        return {'translation': sentence_more_likely, 'neutral': sentence_neutral}

 
def generate_neutral_translation(translation):
        possible_words = get_just_possible_words(translation)
        first_option, second_option, neutral = format_sentence_inflections(possible_words)
    
        return {"first_option": first_option, "second_option": second_option, "neutral": neutral}

def generate_translation_for_poj(source_sentence, google_translation):
    translation_nlp = google_translation
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
    people_control_model = ""
    
    for first_sentence, second_sentence in alignment_model:
        if first_sentence in people_to_neutral_source:
            people_control_model = second_sentence.strip(",").strip(".")
        if first_sentence == sub_split:
            people_model = second_sentence.strip(",").strip(".")

    people_to_neutral= []

    alignment = get_word_alignment_pairs(source_sentence.text, translation_nlp.text, model="bert", matching_methods = "i", align = "itermax")
    people_google = ""

    for first_sentence, second_sentence in alignment:
      first_sent = first_sentence.split('\'')[0]
      if first_sentence in people_to_neutral_source or first_sent in people_to_neutral_source:
        people_to_neutral.append(second_sentence.strip(",").strip("."))
      elif first_sentence == sub_split:
          people_google = second_sentence

    people_model_nlp = get_nlp_pt(people_model)
    people_google_nlp = get_nlp_pt(people_google)

    model_morph = get_morph(people_model_nlp)
    model_google = get_morph(people_google_nlp)

    gender_people_model = get_sentence_gender(people_model_nlp)
    
    print("----> people_model_nlp  ", people_model_nlp)
    print("----> people_google_nlp  ", people_google_nlp)
    print("----> gender_people_model  ", gender_people_model)
    

    if (people_google == None or len(people_google) == 0) and len(people_model_nlp) > 0:
        translation_nlp = translation_model_nlp
    elif len(gender_people_model) > 0 and model_morph != model_google: 
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
        print("----> head_google", head_google)
        print("----> head_model", head_model)
        
        gender_head_google = [token.morph.get("Gender").pop() for token in head_google if len(token.morph.get("Gender")) > 0]
        gender_head_model = [token.morph.get("Gender").pop() for token in head_model if len(token.morph.get("Gender")) > 0]
        
        print("----> gender_head_google", gender_head_google)
        print("----> gender_head_model", gender_head_model)

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
            print(token, "->", token.lemma_,"->", token.head,"->", token.head.lemma_)
            print(people_to_neutral)
            if token.head.text in people_to_neutral or token.head.text[:-1] in people_to_neutral or token.head.lemma_ in people_to_neutral or token.text in people_to_neutral or token.text[:-1] in people_to_neutral or token.lemma_ in people_to_neutral :
                words_to_neutral.append(token)
                index_to_replace.append(index)

    print("----> words_to_neutral  ", words_to_neutral)

    inflections = get_just_possible_words(words_to_neutral)
    print("----> inflections  ", inflections)
    first_sentence, second_sentence, neutral  = format_translations_subjs(index_to_replace, translation_nlp, inflections)
    translation = format_translations_subjs(index_to_replace, translation_nlp, inflections)
    print("----> translation  ", translation)
    
    
    sent = [sentence for sentence in translation if people_control_model in sentence]        
    if second_sentence == sent:
        first_sent = second_sentence
        second_sent = first_sentence
    else:
        first_sent = first_sentence
        second_sent = second_sentence
            

    return {"first_option": first_sent, "second_option": second_sent, "neutral": neutral}

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    sentence_fn = args["--sent"]
    translation_fn = args["--trans"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    sent = get_nlp_en(sentence_fn)
    trans = get_nlp_pt(translation_fn)
    translation = generate_translations_for_score(sent, trans)
    print("###########################")
    print("TRANSLATIONS: ", translation)
    print("###########################")

    logging.info("DONE")