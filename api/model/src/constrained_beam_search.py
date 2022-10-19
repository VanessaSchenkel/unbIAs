import re

# def get_constrained_sentence(translation, nsub):
#     constrained_sentence = ""
#     children = [child for child in nsub[0].children]
#     print("nsub", nsub)
#     print("children", children)

#     for token in translation:
#         if token not in nsub and token not in children:
#             constrained_sentence += token.text_with_ws

#     return constrained_sentence

def get_constrained_sentence(translation, nsub):  
  constrained_sentences = []

  children = [child for child in nsub[0].children]
  new_sentence = ""
  
  for token in translation:
    if token.is_sent_start and token.text.lower() == "eu":
      new_sentence += token.text_with_ws

    if token != nsub[0] and token not in children and token.tag_ != 'ADJ':
      new_sentence += token.text_with_ws
    
    if (token.tag_ == 'ADJ' or token.is_sent_end) and len(new_sentence) > 0:
        lefts = [t for t in token.lefts]
        if len(lefts) > 0 and lefts[0].tag_ == 'DET':
            new_sentence = ""
        else:
            constrained_sentences.append(new_sentence.strip())
            new_sentence = ""

  return constrained_sentences[0]

def get_format_translation(translation, regex = r".,", subst = ","):

    result = re.sub(regex, subst, translation, 0, re.MULTILINE)

    return result    