import torch

from spacy_utils import get_pronoun_on_sentence

def get_disambiguate_pronoun(sentence, pronoun):
    roberta = torch.hub.load('pytorch/fairseq', 'roberta.large.wsc', user_dir='examples/roberta/wsc')
    pronoun_text_formatted = " [" + pronoun.text + "] "
    pronoun_text = " " + pronoun.text + " "
    sentence_text = sentence.text_with_ws.strip(".") + " "
    new_source_sentence = sentence_text.replace(
       pronoun_text, pronoun_text_formatted, 1)
    sentence_formatted = check_if_is_first_in_sentence(new_source_sentence) 
    
    person = roberta.disambiguate_pronoun(sentence_formatted)
    # print("***********************")
    # print("PERSON:", person)
    # print("***********************")

    return person


# roBERTa has a bug, if is the pronoun is the start of the sentence, it crashes
def check_if_is_first_in_sentence(new_source_sentence):
    if len(new_source_sentence) > 0 and new_source_sentence.startswith(" ["):
        return "but " + new_source_sentence
    else:
        return new_source_sentence    