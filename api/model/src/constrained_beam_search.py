from format_translations import format_translations_subjs
from word_alignment import get_word_alignment_pairs
from gender_inflection import get_just_possible_words
from generate_model_translation import generate_translation, get_best_translation
from roberta import get_disambiguate_pronoun
from spacy_utils import get_nlp_en, get_people_source, get_pronoun_on_sentence, get_nlp_pt

def get_constrained_translation(translation, people):
    constrained_sentence = ""
    list_constrained = []

    for token in translation:
        ancestors = [ancestor for ancestor in token.ancestors]
        children = [child for child in token.children]
        # print(token, "--->", ancestors, "--->", children)
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
            new_sentence_model += new_sentence.strip(".").strip() + "."
            return new_sentence_model
    
    return new_sentence_model.replace(".", "").strip() + "." 

def combine_contrained_translations(translations, constrained_splitted, source_sentence, model="bert", matching_methods = "i", align = "itermax", people_model = []):
    first, second = translations
    word_alignments = get_word_alignment_pairs(first.strip(), second.strip(), model=model, matching_methods=matching_methods, align=align)
    new_sentence = ""
    for first_sentence, second_sentence in word_alignments:
        last_word = new_sentence.strip().split(" ")[-1]
        if (first_sentence == second_sentence or first_sentence.strip(",") == second_sentence.strip(",") or first_sentence.strip(".") == second_sentence.strip(".")) and first_sentence != last_word:
            new_sentence += first_sentence + " "
        
        elif len(people_model) > 0 and first_sentence != second_sentence and first_sentence in people_model and first_sentence != last_word:
            new_sentence += first_sentence + " " 
            
        elif len(people_model) > 0 and first_sentence != second_sentence and second_sentence in people_model and second_sentence != last_word:
            new_sentence += second_sentence + " "      

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
        # model_translation = get_best_translation(source_sentence.text_with_ws)
        model_translation = get_best_translation(source_sentence)
        model_alignment = get_word_alignment_pairs(model_translation.strip("."), new_sentence, matching_methods="m", align="mwmf")
        return align_with_model(model_alignment, new_sentence)
    
    return new_sentence.replace(".", "").strip() + "."    

def get_constrained(source_sentence, translation):
    pronoun = get_pronoun_on_sentence(source_sentence)
    
    if len(pronoun) == 0:
        return ""
    
    subj = get_disambiguate_pronoun(source_sentence, pronoun[0])
    masculine_translation, feminine_translation = generate_translation_for_roberta_nsubj(subj)
    translation_nlp = get_nlp_pt(translation)
    constrained_sentence = ""

    for token in translation_nlp:
        head = str(token.head.text)
        if head not in masculine_translation and head not in feminine_translation and token.text not in masculine_translation and token.text not in feminine_translation:
            constrained_sentence += token.text_with_ws
    
    return constrained_sentence


def get_word_to_add(word):
    w = get_nlp_en(word)
    for token in w:
        if token.is_punct:
            return token.text

    word_translatted =  generate_translation(word)
    return word_translatted

def check_constrained_translation(constrained, constrained_translation, source_sentence):
    if len(constrained_translation) > (2*len(source_sentence)) and constrained_translation.endswith(constrained):
        translation = generate_translation(source_sentence)
            
        return translation
    else:
        return constrained_translation   
    
def get_gender_translations(subjects, source_sentence, translation_constrained, people):
        people_to_neutral = []
        source = get_nlp_en(source_sentence)
        source_people = get_people_source(source)

        p = [person.split()[-1] for person in subjects]

        for person in source_people:
            if person.text not in p:
                person_translated = generate_translation(person.text_with_ws)
                person_formatted = person_translated.lower().strip(".")
                people_to_neutral.append(person_formatted[:-1])
                people_to_neutral.append(person_formatted[:-2])
                people_to_neutral.append(person.text)

        words_to_neutral = []
        translation = get_nlp_pt(translation_constrained)
        index_to_replace = []

        for index, token in enumerate(translation):
            # print(token, "->", token.lemma_,"->", token.head,"->", token.head.lemma_)
            if token.head.text in people_to_neutral or token.head.text[:-1] in people_to_neutral or token.head.lemma_ in people_to_neutral or token.text in people_to_neutral or token.text[:-1] in people_to_neutral or token.lemma_ in people_to_neutral :
                words_to_neutral.append(token)
                index_to_replace.append(index)

        inflections = get_just_possible_words(words_to_neutral)
        first_sentence, second_sentence, third_sentence = format_translations_subjs(index_to_replace, translation, inflections)
        
        return first_sentence, second_sentence, third_sentence

def get_constrained_one_subj(translation, people):
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
          

def generate_translation_for_roberta_nsubj(subject):
    translation = generate_translation(subject)
    trans = translation.split()[-1]
    trans_nlp = get_nlp_pt(trans)
    possible_words = get_just_possible_words(trans_nlp)
    
    combined = [j for i in zip(*possible_words) for j in i]

    joined = " ".join(combined)
    splitted_by_dot = joined.split(".")

    return splitted_by_dot[0].strip(), splitted_by_dot[1].strip()