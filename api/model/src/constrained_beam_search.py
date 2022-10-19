from spacy_utils import get_nlp_en


def get_constrained_sentence(translation, nsub):  
  constrained_sentences = []

  children = [child for child in nsub[0].children]
  new_sentence = ""
  
  for token in translation:
    if token != nsub[0] and token not in children and token.tag_ != 'ADJ':
      new_sentence += token.text_with_ws
    
    if (token.tag_ == 'ADJ' or token.is_sent_end) and len(new_sentence) > 0:
        lefts = [t for t in token.lefts]
        if len(lefts) > 0 and lefts[0].tag_ == 'DET':
            new_sentence = ""
        else:
            constrained_sentences.append(new_sentence.strip())
            new_sentence = ""

  return constrained_sentences[0]

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

    splitted = new_sentence.split("###")
    return splitted  


