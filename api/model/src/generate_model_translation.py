"""Usage:
    generate_model_translation.py --sentence=SENTENCE [--debug]
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
    return translation_model


def get_best_translation(source_sentence: str):
    source_sentence = source_sentence if source_sentence.endswith(
        '.') else source_sentence + "."

    input_ids = tokenizer(source_sentence, return_tensors="pt").input_ids

    outputs = model.generate(input_ids, num_beams=10, max_length=10)
    translation_model = tokenizer.batch_decode(
        outputs, skip_special_tokens=True)

    return translation_model[0]


def get_constrained_translation_one_subject(source_sentence, constrained_sentence):
    source_sentence = source_sentence + \
        '.' if not source_sentence.endswith('.') else source_sentence
    force_word = constrained_sentence.strip() + "."

    input_ids = tokenizer(source_sentence, return_tensors="pt").input_ids

    force_words_ids = [
        tokenizer([force_word], add_special_tokens=False).input_ids,
    ]

    outputs = model.generate(
        input_ids,
        force_words_ids=force_words_ids,
        num_beams=10,
        num_return_sequences=2,
        max_new_tokens=200
    )

    most_likely = tokenizer.decode(outputs[0], skip_special_tokens=True)
    less_likely = tokenizer.decode(outputs[1], skip_special_tokens=True)

    return most_likely, less_likely


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    sentence_fn = args["--sentence"]
    debug = args["--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    translation = generate_translation(sentence_fn)
    print(translation)

    logging.info("DONE")
