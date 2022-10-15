"""Usage:
    generate_model_translation.py --st=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = 'VanessaSchenkel/pt-unicamp-handcrafted'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)


def generate_translation(source_sentence):
    translation_model = get_best_translation(source_sentence)
    print(translation_model)


def get_best_translation(source_sentence: str):
    source_sentence = source_sentence if source_sentence.endswith(
        '.') else source_sentence + "."

    input_ids = tokenizer(source_sentence, return_tensors="pt").input_ids

    outputs = model.generate(input_ids, num_beams=10, max_length=10)
    translation_model = tokenizer.batch_decode(
        outputs, skip_special_tokens=True)

    return translation_model


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    st_fn = args["--st"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    generate_translation(st_fn)

    logging.info("DONE")
