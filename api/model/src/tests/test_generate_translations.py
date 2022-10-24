from generate_translations import translate


def test_translate_one_word():
    sentence = "Cat."
    possible_words = translate(sentence)

    assert possible_words['possible_words'] == ['Gato', 'Gata', 'Gat[x]']

def test_translate_one_word_plural():
    sentence = "Cats."
    possible_words = translate(sentence)

    assert possible_words['possible_words'] == ['Gatos', 'Gatas', 'Gat[x]s']

def test_translate_one_sub():
    sentence = "The doctor finished her work."
    translation = translate(sentence)

    assert translation['more_likely'] == 'A médica terminou seu trabalho.'
    assert translation['less_likely'] == 'O médico terminou seu trabalho.'
    assert translation['neutral'] == '[x] médic[x] terminou seu trabalho.'

def test_translate_one_sub_neutral():
    sentence = "The nurse talked a lot"
    translation = translate(sentence)
 
    assert translation['first_option'] == 'A enfermeira falou muito.'
    assert translation['second_option'] == 'O enfermeiro falou muito.'
    assert translation['neutral'] == '[x] enfermeir[x] falou muito.'

def test_translate_one_they():
    sentence = "they are great"
    translation = translate(sentence)
    
    assert translation['first_option'] == 'Eles são ótimos.'
    assert translation['second_option'] == 'Elas são ótimas.'
    assert translation['neutral'] == 'El[x]s são ótim[x]s.'

def test_translate_neutral():
    sentence = "I am tired and I like to read a lot"
    translation = translate(sentence)
    
    assert translation['first_option'] == 'Eu estou cansada e gosto muito de ler.'
    assert translation['second_option'] == 'Eu estou cansado e gosto muito de ler.'
    assert translation['neutral'] == 'Eu estou cansad[x] e gosto muito de ler.'    

def test_translate_she():
    sentence = "She is a good doctor."
    translation = translate(sentence)
    
    assert translation['translation'] == 'Ela é uma boa médica.'
    assert translation['neutral'] == 'El[x] é um[x] bo[x] médic[x].'   

def test_translate_he():
    sentence = "He is a great nurse."
    translation = translate(sentence)

    assert translation['more_likely'] == 'Ele é um ótimo enfermeiro.'
    assert translation['neutral'] == 'É um[x] ótimo enfermeir[x].'     

def test_translate_two_subj_one_pronoun():
    sentence = "The developer argued with the designer because she did not like the design."
    translation = translate(sentence)

    assert translation['first_option'] == 'A desenvolvedora discutiu com o designer porque ela não gostou do design.'
    assert translation['second_option'] == 'A desenvolvedora discutiu com a designer porque ela não gostou do design.'
    assert translation['neutral'] == 'A desenvolvedora discutiu com [x] designer porque ela não gostou do design.'    

def test_translate_more_than_one_gender():
    sentence = "The doctor finished her work but the nurse was still eating his lunch"
    translation = translate(sentence)

    assert translation['translation'] == 'A médica terminou seu trabalho mas o enfermeiro ainda estava almoçando.'
    assert translation['neutral'] == '[x] médic[x] terminou seu trabalho mas [x] enfermeir[x] ainda estava almoçando.'

# def test_translate_with_it():
#     sentence = "The trophy would not fit in the brown suitcase because it was too big."
#     translation = translate(sentence)
#     print(translation)
    
#     assert translation['translation_it'] == 'O troféu não cabia na mala marrom porque era muito grande.'