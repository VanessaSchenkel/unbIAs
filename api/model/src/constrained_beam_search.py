from word_alignment import get_word_alignment_pairs
from gender_inflection import get_just_possible_words
from generate_model_translation import generate_translation, get_best_translation
from translation_google import get_google_translation
from roberta import get_disambiguate_pronoun
from spacy_utils import get_nlp_en, get_pronoun_on_sentence, get_nlp_pt

def get_constrained_translation(translation, people):
    constrained_sentence = ""
    list_constrained = []

    for token in translation:
        ancestors = [ancestor for ancestor in token.ancestors]
        children = [child for child in token.children]
        print(token, "--->", ancestors, "--->", children)
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
            new_sentence_model += new_sentence.strip() + "."
            return new_sentence_model
    
    return new_sentence_model.strip() + "." 

def combine_contrained_translations(translations, constrained_splitted, source_sentence, model="bert", matching_methods = "i", align = "itermax", people_model = []):
    first_translation, second_translation = translations
    word_alignments = get_word_alignment_pairs(first_translation.strip("."), second_translation.strip("."), model=model, matching_methods=matching_methods, align=align)
    new_sentence = ""
    for first_sentence, second_sentence in word_alignments:
        last_word = new_sentence.strip().split(" ")[-1]
        print(first_sentence, "-->", second_sentence)
        print(first_sentence.strip(",") == second_sentence.strip(","))
        if (first_sentence == second_sentence or first_sentence.strip(",") == second_sentence.strip(",") or first_sentence.strip(".") == second_sentence.strip(".")) and first_sentence != last_word:
            new_sentence += first_sentence + " "
        
        elif len(people_model) > 0 and first_sentence != second_sentence and first_sentence in people_model:
            new_sentence += first_sentence + " " 
            
        elif len(people_model) > 0 and first_sentence != second_sentence and second_sentence in people_model:
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
            
    print("new_sentence", new_sentence)

    if len(new_sentence.strip().split(' ')) < len(word_alignments):
        model_translation = get_best_translation(source_sentence.text_with_ws)
        model_alignment = get_word_alignment_pairs(model_translation.strip("."), new_sentence, matching_methods="m", align="mwmf")
        return align_with_model(model_alignment, new_sentence)
    

    print("RETURN NEW SENTENCE:", new_sentence)
    return new_sentence.strip() + "."    

def split_on_subj_and_bsubj(sentence, people):
    sentence_splitted = []
    new_sent = ""   
    
    for token in sentence:
        if token not in people and token.pos_ != "DET":
            new_sent += token.text_with_ws
        elif token.pos_ == "DET" and token.head not in people:
            new_sent += token.text_with_ws
             
        if token.is_sent_end or token in people:
            if len(new_sent) > 0 and new_sent != ".":
                sentence_splitted.append(new_sent.strip())

            new_sent = ""
                       
    return sentence_splitted            


def get_constrained(source_sentence):
    pronoun = get_pronoun_on_sentence(source_sentence)
    
    if len(pronoun) == 0:
        return ""
    
    subj = get_disambiguate_pronoun(source_sentence, pronoun[0])
    masculine_translation, feminine_translation = generate_translation_for_roberta_nsubj(subj)
    translation = get_google_translation(source_sentence.text_with_ws)
    translation_nlp = get_nlp_pt(translation)
    constrained_sentence = ""

    for token in translation_nlp:
        head = str(token.head.text)
        if head not in masculine_translation and head not in feminine_translation and token.text not in masculine_translation and token.text not in feminine_translation:
            constrained_sentence += token.text_with_ws
    
    return constrained_sentence


def get_new_sentence_without_subj(sentence_complete, sentence_to_remove):
    if len(sentence_to_remove) > 0:
        new_sentence = sentence_complete.text.split(sentence_to_remove)[-1]

    else:
        new_sentence = sentence_complete.text

    return get_nlp_en(new_sentence)

def get_subj_subtree(source_sentence, index):
    sentence = ""
  
    for subtree in source_sentence[index].head.subtree:
        sentence += subtree.text_with_ws

    return sentence  


def split_sentences_by_nsubj(source_sentence, subj_list):
    splitted = []
    sentence_complete = source_sentence
    sentence_to_remove = ""

    for sub in subj_list:
        sentence = get_new_sentence_without_subj(sentence_complete, sentence_to_remove)
        for token in sentence:
            if token.text == str(sub):
                sentence_to_remove = get_subj_subtree(sentence, token.i)
                splitted.append(sentence_to_remove)

    return splitted  

def split_sentence_same_subj(sentence):
    new_sentence = ""

    for token in sentence:
        next_token = sentence[-1]
        if not token.is_sent_end:
            next_token = sentence[token.i + 1] 
        if ("PUNCT" == token.pos_ and token.text != ".") and next_token.pos_ != "CCONJ":          
            new_sentence = new_sentence.strip() + "###" + token.text_with_ws
        elif token.pos_ == "CCONJ":
            new_sentence = new_sentence.strip() + "###" + token.text_with_ws
        else:
            new_sentence += token.text_with_ws
    
    if "###" in new_sentence:
        return new_sentence.split("###")

    return new_sentence  


def generate_translation_for_roberta_nsubj(subject):
    translation = generate_translation(subject)
    trans = translation.split()[-1]
    trans_nlp = get_nlp_pt(trans)
    possible_words = get_just_possible_words(trans_nlp)
    
    combined = [j for i in zip(*possible_words) for j in i]

    joined = " ".join(combined)
    splitted_by_dot = joined.split(".")

    return splitted_by_dot[0].strip(), splitted_by_dot[1].strip()