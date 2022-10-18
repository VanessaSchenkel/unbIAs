import re

def get_constrained_sentence(translation, nsub):
    constrained_sentence = ""
    children = [child for child in nsub[0].children]

    for token in translation:
        if token not in nsub and token not in children:
            constrained_sentence += token.text_with_ws

    return constrained_sentence


def get_format_translation(translation, regex = r".,", subst = ","):

    result = re.sub(regex, subst, translation, 0, re.MULTILINE)

    return result    