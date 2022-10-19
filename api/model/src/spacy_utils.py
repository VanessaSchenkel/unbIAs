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
        if token.pos_ == 'PRON':
            pronoun_list.append(token)

    return pronoun_list


def get_nsubj_sentence(sentence):
    nsubj_list = []
    for token in sentence:
        if token.dep_ == 'nsubj':
            nsubj_list.append(token)

    return nsubj_list


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


def get_word_pos_and_morph(word):
    for token in word:
        return token.text, token.pos_, token.morph

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
