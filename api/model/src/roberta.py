import torch

def get_disambiguate_pronoun(sentence, pronoun):
    roberta = torch.hub.load('pytorch/fairseq', 'roberta.large.wsc', user_dir='examples/roberta/wsc')
    pronoun_text_formatted = " [" + pronoun.text + "] "
    pronoun_text = " " + pronoun.text + " "
    new_source_sentence = sentence.text_with_ws.replace(
       pronoun_text, pronoun_text_formatted, 1)
    
    sentence_formatted = check_if_is_first_in_sentence(new_source_sentence)    

    return roberta.disambiguate_pronoun(sentence_formatted)


# roBERTa has a bug, if is the pronoun is the start of the sentence, it crashes
def check_if_is_first_in_sentence(new_source_sentence):
    if new_source_sentence.startswith(" ["):
        return "but " + new_source_sentence
    else:
        return new_source_sentence    