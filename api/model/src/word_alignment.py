"""Usage:
    word_alignment.py --first_sentence=SOURCE --second_sentence=TARGET [--debug]
"""
# External imports
import logging
from docopt import docopt
from simalign import SentenceAligner


def initialize(first_sentence, second_sentence):
    myaligner = SentenceAligner(model="bert", token_type="bpe", matching_methods="mai")
    alignments = myaligner.get_word_aligns(first_sentence, second_sentence)
    return alignments['itermax']

def get_word_alignment_pairs(first_sentence, second_sentence):
    print("Possible Alignments From SimAlign")
    print("Word in Sent 1 -----> Word in Sent 2")
    sent1 = []
    sent2 = []
    source_tokens = first_sentence.split(' ')
    target_tokens = second_sentence.split(' ')
    alignments = initialize(source_tokens, target_tokens)
    for item in alignments:
     print(source_tokens[item[0]],"---------->", target_tokens[item[1]])
     sent1.append(source_tokens[item[0]])
     sent2.append(target_tokens[item[1]])

    word_align_pairs = zip(sent1,sent2)
    return list(word_align_pairs) 

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    first_sentence_fn = args["--first_sentence"]
    second_sentence_fn = args["--second_sentence"]
    debug = args["--debug"]


    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    word_alignment = get_word_alignment_pairs(first_sentence_fn, second_sentence_fn)
    print(word_alignment)

    logging.info("DONE")    