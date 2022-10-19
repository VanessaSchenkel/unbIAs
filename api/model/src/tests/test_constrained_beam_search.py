from spacy_utils import get_nlp_en, get_nlp_pt, get_nsubj_sentence
from constrained_beam_search import get_constrained_sentence, split_sentences_by_nsubj, split_sentence_same_subj


def test_split_sentence_same_subj():
    sentence = get_nlp_en("I am tired, but I have to finish this tests")
    list_sentence = split_sentence_same_subj(sentence)
    assert len(list_sentence) == 3

def test_split_sentence_same_subj_without_comma():
    sentence = get_nlp_en("I am tired but I have to finish this tests")
    list_sentence = split_sentence_same_subj(sentence)
    assert len(list_sentence) == 2

def test_split_sentence_same_subj_one_sentence():
    sentence = get_nlp_en("I am tired")
    list_sentence = split_sentence_same_subj(sentence)
    assert len(list_sentence) == 1

def test_get_constrained_sentence():
    sentence = get_nlp_pt("O médico terminou seu trabalho.")
    subjs = get_nsubj_sentence(sentence)

    constrained = get_constrained_sentence(sentence, subjs)
    
    assert constrained == "terminou seu trabalho."

def test_get_constrained_sentence():
    sentence = get_nlp_pt("A médica inteligente terminou seu trabalho.")
    subjs = get_nsubj_sentence(sentence)

    constrained = get_constrained_sentence(sentence, subjs)
    
    assert constrained == "terminou seu trabalho."    

# def test_split_sentences_by_nsubj():
#     sentence = get_nlp_pt("A médica terminou seu trabalho, mas a enfermeira ainda não.")
#     subjs = get_nsubj_sentence(sentence)

#     splitted = split_sentences_by_nsubj(sentence, subjs)
    
#     assert len(splitted) == 2    
