

def make_neutral(word):
    new_sentence = ""
    for token in sentence:
        gender = token.morph.get("Gender")
        if len(gender) > 0 and token.text.lower() != "eu":
            if token.text.endswith("o") or token.text.endswith("a"):
                new_word = token.text[:-1] + "X"
                new_sentence += new_word + " "
            elif token.text.endswith("os") or token.text.endswith("as"):
                new_word = token.text[:-1] + "Xs"
                new_sentence += new_word + " "
        else:
            new_sentence += token.text_with_ws

    return new_sentence
