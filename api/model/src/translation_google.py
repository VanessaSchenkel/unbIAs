
def translate_google_just_one_word(source_sentence):
    translation = ""


def translate_text(text):
    """Translates text into the target language.
    """
    import six
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()

    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(text, source_language="en", target_language="pt-BR")

    print(u"result: {}".format(result))
    print(u"Text: {}".format(result["input"]))
    print(u"Translation: {}".format(result["translatedText"]))
