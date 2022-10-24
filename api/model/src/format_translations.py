import itertools

from spacy_utils import get_nlp_pt, get_nlp_en

def format_sentence(sentence):
    new_sentence = ""
    for token in sentence:
        if "CONJ" in token.pos_:          
            new_sentence = new_sentence.strip() + "###" + token.text_with_ws
        else:
            new_sentence += token.text_with_ws

    splitted = new_sentence.split("###")
    return splitted  

def format_with_dot(translation):
    sentence = get_nlp_pt(translation)
    new_sentence = ""
    for token in sentence:
        if token.text == "." and token.i != len(sentence)-1:
            next_token = sentence[token.i + 1]
            if next_token.tag_ != "CCONJ" and not next_token.is_punct and not next_token.is_lower:
                new_sentence += token.text_with_ws
            else:
                new_sentence += " "
        else:
            if token.ent_type_ == "PERSON" or token.is_sent_start:
                new_sentence += token.text_with_ws
            else:
                 new_sentence += token.text_with_ws.lower()

    return new_sentence          

def format_multiple_sentence(translations):
    sentences_formatted = []

    all_combinations = list(itertools.product(*translations))
    
    for sentence in all_combinations:
        sent_joined = " ".join(sentence)
        formatted = format_with_dot(sent_joined)
        sentences_formatted.append(formatted)

    return sentences_formatted

def should_remove_first_word(sentence):
    sent = get_nlp_en(sentence)
    for token in sent:
        return (token.pos_ == "CCONJ" or token.is_punct) and token.i == 0

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