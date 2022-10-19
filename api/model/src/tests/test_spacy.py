from spacy_utils import has_gender_in_source, is_all_same_pronoun, get_noun_chunks, get_pronoun_on_sentence, get_nlp_en, get_nlp_pt, get_nsubj_sentence, get_noun_sentence, get_sentence_gender


def test_has_gender_in_source():
    sentence = "The doctor finished her work"
    assert has_gender_in_source(sentence) == True

def test_not_has_gender_in_source():
    sentence = "I am hungry"
    assert has_gender_in_source(sentence) == False

def test_get_pronoun_on_sentence():
    sentence = get_nlp_en("I am hungry and you are tired but she is cool")
    assert len(get_pronoun_on_sentence(sentence)) == 3

def test_get_pronoun_on_sentence_without_it():
    sentence = get_nlp_en("The cat")
    assert len(get_pronoun_on_sentence(sentence)) == 0

def test_nsubj_sentence():
    sentence = get_nlp_en("The doctor was sleeping, the nurse is working")
    subjs = get_nsubj_sentence(sentence)
    
    assert len(subjs) == 2

def test_noun_sentence():
    sentence = get_nlp_en("The sofa was comfy")
    nouns = get_noun_sentence(sentence)

    assert len(nouns) == 1

def test_get_sentence_gender_eu():
    sentence = get_nlp_pt("Eu")
    genders = get_sentence_gender(sentence)
    
    assert len(genders) == 0

def test_get_sentence_gender_voce():
    sentence = get_nlp_pt("Você")
    genders = get_sentence_gender(sentence)
    
    assert len(genders) == 0    

def test_get_sentence_gender():
    sentence = get_nlp_pt("médica")
    genders = get_sentence_gender(sentence)
    
    assert len(genders) == 1    

def test_is_all_same_pronoun_en():
    sentence = get_nlp_en("The doctor finished her work")
    pronouns = is_all_same_pronoun(sentence)
    
    assert pronouns == True 

def test_get_noun_chunks():
    sentence = get_nlp_en("The doctor finished her work and the nurse was eating her lunch")
    nouns = get_noun_chunks(sentence)
    
    assert len(nouns) == 4