
"""Usage:
    translation_google.py --sentence=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt
from spacy_utils import get_nlp_pt

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
    print("RESULT:", result["translatedText"])
    return result["translatedText"]


def get_google_translation(source_sentence):
    translation = translate_text(source_sentence) 
    translation = translation + '.' if not translation.endswith('.') else translation
    sentence_formatted = check_I(source_sentence, translation) 

    sentence_nlp = get_nlp_pt(sentence_formatted)
   
    return sentence_nlp

def check_I(source_sentence, translation):
    if source_sentence.startswith("I") or source_sentence.startswith("I'm") and not translation.lower().startswith("eu"):
        return "Eu " + translation.lower()
    else:
        return translation    


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    sentence_fn = args["--sentence"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    translation = get_google_translation(sentence_fn)
    print(translation)

    logging.info("DONE")