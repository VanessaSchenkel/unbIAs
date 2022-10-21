from gender_inflection import get_just_possible_words
from generate_model_translation import generate_translation
from translation_google import get_google_translation
from roberta import get_disambiguate_pronoun
from spacy_utils import get_nlp_en, get_nsubj_sentence, get_pronoun_on_sentence, get_nlp_pt

def get_constrained_sentence(translation, nsub):  
  constrained_sentences = []

  children = [child for child in nsub[0].children]
  new_sentence = ""
  pronoun = get_nsubj_sentence(translation)
  
  for token in translation:
    print("====", token, token.pos_, token.morph, token.dep_, children, token.head)
    
    if token != nsub[0] and token not in children and token.pos_ != 'ADJ':
      new_sentence += token.text_with_ws
    
    if (token.pos_ == 'ADJ' or token.is_sent_end) and len(new_sentence) > 0:
        lefts = [t for t in token.lefts]
        
        if len(lefts) > 0 and lefts[0].pos_ == 'DET':
            new_sentence = ""
        else:
            constrained_sentences.append(new_sentence.strip())
            new_sentence = ""

  return constrained_sentences[0]


def get_constrained_gender(translation):
    head = ""
    word = ""
    for token in translation:
        if token.pos_ == "PRON" and token.dep_ == "nsubj":
            head = str(token.head.text)
        elif token.text == head and token.dep_ == "ROOT":
            word = token.text
    
    return word        

def get_constrained(source_sentence):
    source_nlp = get_nlp_en(source_sentence)
    pronoun = get_pronoun_on_sentence(source_nlp)
    print("pronoun --", pronoun)
    if len(pronoun) == 0:
        return ""
    
    subj = get_disambiguate_pronoun(source_nlp, pronoun[0].text)
    print("subj --", subj)

    masculine_translation, feminine_translation = generate_translation_for_roberta_nsubj(subj)
    translation = get_google_translation(source_sentence)
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
    # is_all_the_same = is_all_same_pronoun(source_sentence)

    # print(is_all_the_same, "is_all_the_same")
    # if is_all_the_same:
    #     return [source_sentence.text_with_ws]

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
        if "CCONJ" == token.pos_ or ("PUNCT" == token.pos_ and token.text != "."):          
            new_sentence = new_sentence.strip() + "###" + token.text_with_ws
        else:
            new_sentence += token.text_with_ws
    
    if "###" in new_sentence:
        return new_sentence.split("###")

    return new_sentence  


def generate_translation_for_roberta_nsubj(subject):
    translation = generate_translation(subject)
    translation = get_nlp_pt(translation)
    possible_words = get_just_possible_words(translation)

    combined = [j for i in zip(*possible_words) for j in i]

    joined = " ".join(combined)
    splitted_by_dot = joined.split(".")

    return splitted_by_dot[0].strip(), splitted_by_dot[1].strip()