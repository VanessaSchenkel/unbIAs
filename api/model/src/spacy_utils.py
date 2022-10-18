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
        print(token, token.dep_)
        if token.dep_ == 'nsubj':
            nsubj_list.append(token)

    return nsubj_list


def get_noun_sentence(sentence):
    noun_list = []
    for token in sentence:
        if token.tag_ == 'NOUN':
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
        if len(gender) > 0:
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
    # is_all_the_same = is_all_same_pronoun(source_sentence)

    # print(is_all_the_same, "is_all_the_same")
    # if is_all_the_same:
    #     return [source_sentence.text_with_ws]

    for sub in subj_list:
        sentence = get_new_sentence_without_subj(sentence_complete, sentence_to_remove)
        print(sentence)
        for token in sentence:
            if token.text == str(sub):
                sentence_to_remove = get_subj_subtree(sentence, token.i)
                splitted.append(sentence_to_remove)

    return splitted


def format_sentence(sentence):
    new_sentence = ""
    for token in sentence:
        if "CONJ" in token.pos_:          
            new_sentence = new_sentence.strip() + "###" + token.text_with_ws
        else:
            new_sentence += token.text_with_ws

    splitted = new_sentence.split("###")

    return splitted  