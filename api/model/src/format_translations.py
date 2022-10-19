import itertools
import re

from spacy_utils import get_nlp_pt

def format_sentence(sentence):
    new_sentence = ""
    for token in sentence:
        if "CONJ" in token.pos_:          
            new_sentence = new_sentence.strip() + "###" + token.text_with_ws
        else:
            new_sentence += token.text_with_ws

    splitted = new_sentence.split("###")
    return splitted  

def get_format_translation(translation, regex = r".,", subst = ","):
    result = re.sub(regex, subst, translation, 0, re.MULTILINE)

    return result  

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

def format_multiple_sentence(translations):
    sentences_formatted = []

    all_combinations = list(itertools.product(*translations))
    
    for sentence in all_combinations:
        sent_joined = " ".join(sentence)
        formatted = format_with_dot(sent_joined)
        sentences_formatted.append(formatted)

    return sentences_formatted
            