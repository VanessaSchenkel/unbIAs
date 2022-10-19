import torch


def get_disambiguate_pronoun(sentence, pronoun):
    roberta = torch.hub.load('pytorch/fairseq', 'roberta.large.wsc', user_dir='examples/roberta/wsc')
    pronoun_text_formatted = " [" + pronoun + "] "
    pronoun_with_space = " " + pronoun + " "
    new_source_sentence = sentence.text_with_ws.replace(
        pronoun_with_space, pronoun_text_formatted)
    
    return roberta.disambiguate_pronoun(new_source_sentence)

