"""Usage:
    generate_model_translation.py --sentence=SENTENCE [--debug]
"""

# External imports
import logging
from docopt import docopt
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, DisjunctiveConstraint

model_name = 'VanessaSchenkel/pt-unicamp-handcrafted'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)


def generate_translation(source_sentence, num_return_sequences = 1):
    translation_model = get_best_translation(
        source_sentence, num_return_sequences)
    return translation_model


def get_best_translation(source_sentence: str, num_return_sequences=1):
    source_sentence = source_sentence if source_sentence.endswith(
        '.') else source_sentence + "."

    input_ids = tokenizer(source_sentence, return_tensors="pt").input_ids

    outputs = model.generate(
        input_ids,
        num_beams=10,
        num_return_sequences=num_return_sequences,
        max_new_tokens=200
    )

    if num_return_sequences == 1:
        return tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

    translation_model = []

    for output in outputs:
        translation_model.append(tokenizer.decode(
            output, skip_special_tokens=True))

    return translation_model


def get_constrained_translation_one_subject(source_sentence, constrained_sentence):
    source_sentence = source_sentence.strip() + "."
  
    input_ids = tokenizer(source_sentence, return_tensors="pt").input_ids

    force_words_ids = [
        tokenizer(constrained_sentence, add_special_tokens=False).input_ids,
    ]

    outputs = model.generate(
        input_ids,
        force_words_ids=force_words_ids,
        num_beams=50,
        num_return_sequences=2,
        no_repeat_ngram_size=5,
        max_new_tokens=500
    )

    most_likely = tokenizer.decode(outputs[0], skip_special_tokens=True)
    less_likely = tokenizer.decode(outputs[1], skip_special_tokens=True)

    return most_likely, less_likely


def generate_translation_with_gender_constrained(source_sentence, constrained_gender):
    source_sentence = source_sentence + \
        '.' if not source_sentence.endswith('.') else source_sentence
    
    input_ids = tokenizer(source_sentence, return_tensors="pt").input_ids
    
    force_words_ids = tokenizer(
        [constrained_gender], add_special_tokens=False).input_ids

    outputs = model.generate(
        input_ids,
        force_words_ids=force_words_ids,
        num_beams=20,
        num_return_sequences=3,
        max_new_tokens=200
    )

    most_likely = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return most_likely

def get_contrained_translation(source, constrained_sentence):
    source = source.strip() + "."
    constrained_sentence = constrained_sentence.strip().lstrip(",") + "."
    
    input_ids = tokenizer(source, return_tensors="pt").input_ids

    force_words_ids = [
        tokenizer([constrained_sentence], add_special_tokens=False).input_ids,
    ]

    output = model.generate(
        input_ids,
        force_words_ids=force_words_ids,
        num_beams=20,
        num_return_sequences=3,
        max_new_tokens=50
    )

  
    translation = tokenizer.decode(output[0], skip_special_tokens=True)
    
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

    translation = generate_translation(sentence_fn)
    print(translation)

    logging.info("DONE")
