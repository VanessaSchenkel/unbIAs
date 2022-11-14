import torch

from spacy_utils import get_only_subject_sentence, get_pronoun_on_sentence

def get_disambiguate_pronoun(sentence, pronoun):
    roberta = torch.hub.load('pytorch/fairseq', 'roberta.large.wsc', user_dir='examples/roberta/wsc', verbose=False)
    pronoun_text_formatted = " [" + pronoun.text + "] "
    # print("pronoun_text_formatted::::", pronoun_text_formatted)
    pronoun_text = " " + pronoun.text + " "
    # print("pronoun_text::::", pronoun_text)
    sentence_text = " "+ sentence.text_with_ws.strip(".") + " "
    # print("sentence_text::::", sentence_text)
    new_source_sentence = sentence_text.replace(
       pronoun_text, pronoun_text_formatted, 1)
    # print("new_source_sentence::::", new_source_sentence)
    
    sentence_formatted = check_if_is_first_in_sentence(new_source_sentence) 
    # print("sentence_formatted::::", sentence_formatted)
    try:
        person = roberta.disambiguate_pronoun(sentence_formatted)
        # print("***********************")
        # print("PERSON:", person)
        # print("***********************")

        return person
    except:
        # print("ROBERTA EXCEPTION")
        nsubj = get_only_subject_sentence(sentence)
        return nsubj.text
        

def get_subject_source(source_sentence):
    pronouns = get_pronoun_on_sentence(source_sentence)
    subjects = []
    for pronoun in pronouns:
        subject = get_disambiguate_pronoun(source_sentence, pronoun)
        subjects.append(subject)
    
    # print("SUBJECTS", subjects)
    sub_split = subjects[0].split()[-1]
    return sub_split

# roBERTa has a bug, if is the pronoun is the start of the sentence, it crashes
def check_if_is_first_in_sentence(new_source_sentence):
    if len(new_source_sentence) > 0 and new_source_sentence.startswith(" ["):
        return "but " + new_source_sentence
    else:
        return new_source_sentence    