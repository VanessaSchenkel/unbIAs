




from model.src.translation_google import translate_text


def get_source_sentence(source_sentence):
    print(source_sentence)
    if ' ' not in source_sentence.strip():
        print("sem ESPAÇO")
        translate_text(source_sentence)
    
