from spacy_utils import get_nlp_en

def format_sentence(sentence):
    new_sentence = ""
    for token in sentence:
        if "CONJ" in token.pos_ or "PUNCT" in token.pos_:          
            new_sentence = new_sentence.strip() + "###" + token.text_with_ws
        else:
            new_sentence += token.text_with_ws

    splitted = new_sentence.split("###")
    return splitted  
   
def should_remove_first_word(sentence):
    sent = get_nlp_en(sentence)
    for token in sent:
        return (token.pos_ == "CCONJ" or token.is_punct) and token.i == 0

def should_remove_last_word(sentence):
    sent = get_nlp_en(sentence)
    for token in sent:
        return (token.pos_ == "CCONJ" or token.is_punct) and token.is_sent_end

def format_translations_subjs(index_to_replace, sentence, inflections):
    translations = []

    for id in range(3):
        new_sentence = ""
        cont = 0
        for index, word in enumerate(sentence):
            if index not in index_to_replace:
                new_sentence += word.text_with_ws
            else:
                new_sentence += inflections[cont][id] + " "
                cont = cont + 1
        sentence_formatted = new_sentence[0].capitalize() + new_sentence[1:]
        translations.append(sentence_formatted)

    return translations