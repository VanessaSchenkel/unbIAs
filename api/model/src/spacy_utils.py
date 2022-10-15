import spacy


nlp = spacy.load("pt_core_news_lg")
nlp_en = spacy.load("en_core_web_lg")


def get_nlp_en(sentence):
    return nlp_en(sentence)


def get_nlp_pt(sentence):
    return nlp(sentence)


def has_gender_in_source(word):
    return True


def get_pronoun_on_sentence(sentence):
    pronoun_list = []
    for token in sentence:
        if token.pos_ == 'PRON':
            pronoun_list.append(token)

    return pronoun_list


def get_nsubj_sentence(sentence):
    nsubj_list = []
    for token in sentence:
        if token.dep_ == 'nsubj':
            nsubj_list.append(token)
    
    return nsubj_list        


def get_sentence_gender(sentence):
    gender_list = []
    for token in sentence:
        gender = token.morph.get("Gender")
        if len(gender) > 0:
            gender_list.append(gender.pop())

    return gender_list