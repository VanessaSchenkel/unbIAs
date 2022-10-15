import torch

roberta = torch.hub.load(
    'pytorch/fairseq', 'roberta.large.wsc', user_dir='examples/roberta/wsc')


def get_disambiguate_pronoun(sentence, pronoun):
    pronoun_text_formatted = "[" + pronoun.text + "]"
    new_source_sentence = sentence.text.replace(
        pronoun.text, pronoun_text_formatted)
    return roberta.disambiguate_pronoun(new_source_sentence)