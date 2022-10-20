from generate_translations import translate


def test_translate_one_word():
    sentence = "Cat."
    possible_words = translate(sentence)

    assert possible_words['possible_words'] == ['gato', 'gata', 'gat[X]']

def test_translate_one_word_plural():
    sentence = "Cats."
    possible_words = translate(sentence)

    assert possible_words['possible_words'] == ['gatos', 'gatas', 'gat[X]s']

def test_translate_one_sub():
    sentence = "The doctor finished her work."
    translation = translate(sentence)

    assert translation['more_likely'] == 'A médica terminou seu trabalho.'
    assert translation['less_likely'] == 'O médico terminou seu trabalho.'
    assert translation['neutral'] == '[X] médic[X] terminou seu trabalho.'

def test_translate_one_sub_neutral():
    sentence = "The nurse talked a lot"
    translation = translate(sentence)
 
    assert translation['first_option'] == 'A enfermeira falou muito.'
    assert translation['second_option'] == 'O enfermeiro falou muito.'
    assert translation['neutral'] == '[X] enfermeir[X] falou muito.'

def test_translate_one_they():
    sentence = "they are great"
    translation = translate(sentence)
    
    assert translation['first_option'] == 'Eles são ótimos.'
    assert translation['second_option'] == 'Elas são ótimas.'
    assert translation['neutral'] == 'El[x]s são ótim[x]s.'

def test_translate_neutral():
    sentence = "I am tired and I like to read a lot"
    translation = translate(sentence)
    
    assert translation['first_option'] == 'Eu estou cansada e eu gosto de ler muito.'
    assert translation['second_option'] == 'Eu estou cansado e eu gosto de ler muito.'
    assert translation['neutral'] == 'Eu estou cansad[X] e eu gosto de ler muito.'    

def test_translate_she():
    sentence = "She is a good doctor."
    translation = translate(sentence)
    
    assert translation['more_likely'] == 'Ela é uma boa médica.'
    assert translation['less_likely'] == 'Ela é um bom médico.'
    assert translation['neutral'] == 'El[X] é um[X] médic[X] .'   

# def test_translate_with_it():
#     sentence = "The trophy would not fit in the brown suitcase because it was too big."
#     translation = translate(sentence)
#     print(translation)
    
#     assert translation['translation_it'] == 'O troféu não cabia na mala marrom porque era muito grande.'