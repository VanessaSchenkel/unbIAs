"""Usage:
    spacy_utils.py --sentence=SENTENCE --lang=LANGUAGE [--debug]
"""

# External imports
import logging
from docopt import docopt
import pandas as pd
from IPython.display import display
import spacy

nlp = spacy.load("pt_core_news_lg")
nlp_en = spacy.load("en_core_web_lg")

def get_nlp_en(sentence):
    return nlp_en(sentence)

def get_nlp_pt(sentence):
    return nlp(sentence)

def has_gender_in_source(sentence):
    sentence_nlp = get_nlp_en(sentence)
    return len(get_sentence_gender(sentence_nlp)) > 0

def get_pronoun_on_sentence(sentence):
    pronoun_list = []
    for token in sentence:
        if token.pos_ == 'PRON' and token.tag_ != 'NN':
            pronoun_list.append(token)

    return pronoun_list


def get_nsubj_sentence(sentence):
    nsubj_list = []
    for token in sentence:
        if token.dep_ == 'nsubj':
            nsubj_list.append(token)

    return nsubj_list

def get_noun_sentence(sentence):
    noun_list = []
    for token in sentence:
        if token.pos_ == 'NOUN':
            noun_list.append(token)

    return noun_list


def get_only_subject_sentence(sentence):
    for token in sentence:
        if token.dep_ == 'nsubj':
            return token


def get_sentence_gender(sentence):
    gender_list = []
    for token in sentence:
        gender = token.morph.get("Gender")

        #spacy says eu is masculine
        if len(gender) > 0 and token.text.lower() != "eu":
            gender_list.append(gender.pop())

    return gender_list

def is_plural(word):
    for token in word:
        number = token.morph.get("Number")
        return "Plur" in number 

def get_word_pos_and_morph(word):
    return word.text, word.pos_, word.morph

def is_all_same_pronoun(sentence):
    pronoun_list = []
    for token in sentence:
        if token.pos_ == 'PRON':
            pronoun_list.append(token.text)

    return len(set(pronoun_list)) == 1

def get_noun_chunks(sentence):
    chunk_list = []
    for chunk in sentence.noun_chunks:
        chunk_list.append(chunk)

    return chunk_list 

def get_pobj(sentence):
    pobj_list = []
    for token in sentence:
        if token.dep_ == "pobj":
             pobj_list.append(token)

    return pobj_list  

def get_people(sentence):
    people = []
    for token in sentence:
        # print(token, token.pos_, token.dep_, token.head)
        if (token.dep_ == "nsubj" and token.pos_ == "NOUN") or (token.dep_ == "obl" and token.pos_ == "NOUN") or token.text.lower() == "eu":
            people.append(token)
    
    return people     
    
def check_word(token_before, token, dep, next_token):
    return token.dep_ == dep and token.pos_ == "NOUN" and "PRON" not in token.pos_ and token_before.pos_ != "VERB" and not token.is_sent_end and next_token.pos_ != "PUNCT" and next_token.pos_ != "ADP" and next_token.pos != "AUX" and token_before.pos_ != "PART" or (next_token.pos_ == "PART" and token.pos_ != "VERB")

def get_people_source(sentence):
    source = sentence.text_with_ws.strip(".")
    doc = get_nlp_en(source)
    people = []
    for token in doc:
        next_token = doc[-1]
        token_before = doc[0]
        if not token.is_sent_end:
            next_token = doc[token.i + 1] 
        if not token.is_sent_start: 
            token_before = doc[token.i - 1]
        # print(token, token.pos_, token.dep_, token_before.pos_, next_token.pos_)    
        if (token.pos_ == "NOUN") and (token.dep_ == "nsubj" and next_token.pos_ != "AUX" or (token.dep_ == "obl" and token.pos_ == "NOUN") or check_word(token_before, token, "pobj", next_token) or check_word(token_before, token, "dobj", next_token)):
            people.append(token)

        #exception, spacy don't recognize cleaner as noun    
        elif token.text == "cleaner":
            people.append(token)
    
    return people        

def get_all_information(sentence):
    for token in sentence:
        children = [child for child in token.children]
        print("---> Token:", token)   
        print("-> Pos:", token.pos_, "-> Head:", token.head)   
        print("-> Lemma:", token.lemma_)   
        print("-> Morph:", token.morph)  
        print("-> Children:", children)   

def display_with_pd(sentence):
    table = {}
    text_list = []
    anc = []
    child = []
    dep = []
    head = []
    morph = []
    pos = []

    for token in sentence:
        text_list.append(token.text)
        anc.append([ancestor for ancestor in token.ancestors])
        child.append([child for child in token.children])
        dep.append(token.dep_)
        head.append(token.head)
        morph.append(token.morph)
        pos.append(token.pos_)

    table['text'] = text_list
    table['anc'] = anc
    table['child'] = child
    table['dep'] = dep
    table['head'] = head
    table['morph'] = morph
    table['pos'] = pos


    df = pd.DataFrame(table)

    display(df)

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    sentence_fn = args["--sentence"]
    language_fn = args["--lang"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if 'pt' == language_fn:
        sentence = get_nlp_pt(sentence_fn)
    else:
        sentence = get_nlp_en(sentence_fn)

    display_with_pd(sentence)
    print("------------------------")
    people = get_people_source(sentence)
    print("people:", people)
    print("------------------------")
    noun = get_noun_chunks(sentence)
    print("noun:", noun)

    logging.info("DONE")