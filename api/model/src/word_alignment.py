"""Usage:
    word_alignment.py --first_sentence=SOURCE --second_sentence=TARGET [--debug]
"""
# External imports
import logging
from docopt import docopt
from simalign import SentenceAligner

from spacy_utils import get_people_source

#matching-methods = "m: Max Weight Matching (mwmf), a: argmax (inter), i: itermax, f: forward (fwd), r: reverse (rev)"
def initialize(first_sentence, second_sentence, model, matching_methods, align):
    myaligner = SentenceAligner(model=model, token_type="bpe", matching_methods=matching_methods)
    alignments = myaligner.get_word_aligns(first_sentence, second_sentence)
    return alignments[align]

def get_word_alignment_pairs(first_sentence, second_sentence, model="bert-base-uncased", matching_methods = "i", align = "itermax"):
    source_tokens, target_tokens = format_sentences(first_sentence, second_sentence)
    sent1 = []
    sent2 = []
    # print("Possible Alignments From SimAlign")
    # print("Word in Sent 1 -----> Word in Sent 2")
    alignments = initialize(source_tokens, target_tokens, model, matching_methods, align)
    for item in alignments:
    #  print(source_tokens[item[0]],"---------->", target_tokens[item[1]])
     sent1.append(source_tokens[item[0]])
     sent2.append(target_tokens[item[1]])

    word_align_pairs = zip(sent1,sent2)
    return list(word_align_pairs) 

def format_sentences(first_sentence, second_sentence):
    sent1 = first_sentence.split()
    sent2 = second_sentence.split()

    if len(sent1) >= len(sent2):
        return sent1, sent2
    else:
        return sent2, sent1

def get_align_people(source_sentence, translation_sentence):
    word_alignments = get_word_alignment_pairs(source_sentence.text_with_ws, translation_sentence.text_with_ws, model="bert", matching_methods = "i", align = "itermax")
    source_people = get_people_source(source_sentence)
    people = [token.text for token in source_people]
    people_align = []
    for sent1, sent2 in word_alignments:
        if sent1 in people: 
            people_align.append(sent2)
        elif sent2 in people:  
            people_align.append(sent1)  

    people_list = []
    for token in translation_sentence:
        if token.text in people_align:
            people_list.append(token)

    return people_list   

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