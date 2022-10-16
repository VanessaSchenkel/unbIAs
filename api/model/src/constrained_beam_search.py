

def get_constrained_sentence(translation, nsub):
    constrained_sentence = ""
    children = [child for child in nsub[0].children]
    for token in translation:
        if token not in nsub and token not in children:
            constrained_sentence += token.text + " "

    return constrained_sentence


    