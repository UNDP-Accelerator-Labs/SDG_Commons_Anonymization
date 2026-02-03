from os import listdir
from os.path import join, dirname, isfile, exists
import json
from sys import path as syspath
from pprint import pprint

from colorama import Fore # this is to colorize the terminal output

syspath.append(dirname(__file__))
import _01_agent
from _02_checker import checker
from utils import editableInput, getData, getPartnerType

WORKING = True


def human_in_the_loop(text, AI=True):
  print(Fore.CYAN + text)
  if AI == True:
    extracted_entities = _01_agent.LLM(text)
    # extracted_entities = _01_agent.LLM(text, stream_output=True)
  else:
    extracted_entities = [text.strip()]

  print(extracted_entities)
  user_validation = editableInput('edit: ', json.dumps(extracted_entities))
  # User validation
  if len(user_validation.strip()) != 0:
    try:
      entity = json.loads(user_validation)
      print(Fore.GREEN, entity, Fore.WHITE)
    except:
      print(Fore.RED, 'There is a json error', Fore.WHITE)
      user_validation = editableInput('edit: ', json.dumps(extracted_entities))
      entity = json.loads(user_validation)
      print(Fore.GREEN, entity, Fore.WHITE)
  else:
    entity = []
  return entity

def parsePIID(items,case):
  full_text = "\n".join([str(i.get("txt", "")).strip() for i in items if i.get("txt", None) is not None and str(i.get("txt", "")).strip() != ""])
  
  conversation = [
    {"role": "user", "content": f"TEXT TRANSCRIPT: {full_text}"},
  ]
  
  piid, conversation = _01_agent.LLM(conversation, stream_output=True)
  pii = piid["list"]
  r = piid["reasoning"]
  pcis = _01_agent.regex(full_text)

  piis = list(set(pii + pcis))
  print(Fore.RED + str(pii) + Fore.WHITE)

  # piis = human_in_the_loop(full_text)
        
  return (len(pii) > 0, pii, full_text, conversation, r)

def getPIID(data,**kwargs):
  data_keys = kwargs.get("data_keys", None)
  stream_output = kwargs.get("stream_output", False)

  if data_keys is None:
    instructions_only = True
  else:
    instructions_only = False
  pid = data.get("pad_id", None)
  iso3 = data.get("iso3", "NUL")
  date = data.get("created_at", None)
  print(iso3, date, pid)
  sections = data.get("sections", [])

  for s in sections:
    title = s.get("title", "")
    items = s.get("items", [])
    
    if len(items) == 1 and items[0].get("type", "").lower() == 'group':
      i = items[0]
      sub_item_list = i.get("items", [])
      contains_pii = False
      pii = []
      for sub_items in sub_item_list:
        if instructions_only == True:
          instructions = [si.get("instruction", None) for si in sub_items]
        else:
          c, p, t, conversation, r = parsePIID(sub_items, case=len(data_keys))
          contains_pii = contains_pii or c
          pii = pii + p
      
    elif len(items) == 1 and items[0].get("type", "").lower() == 'group':
      print('Contains a group and something else. This is an edge case that needs attention.')
    else:
      if instructions_only == True:
        instructions = [i.get("instruction", None) for i in items]
      else:
        contains_pii, pii, t, conversation, r = parsePIID(items, case=len(data_keys))

  if instructions_only == True:
    return list(set(instructions))
  else:
    if contains_pii == True:
      if stream_output == True:
        print(Fore.RED + f"{pid} contains PII")
        print(Fore.CYAN + ", ".join(pii) + Fore.WHITE)
      return ({ "pid": pid, "pii": pii, "transcript": t, "reasoning": r }, conversation)
    else: 
      return ({ "pid": pid, "pii": None, "transcript": t, "reasoning": r }, conversation)

if __name__ == "__main__":
  source_dir = join(dirname(__file__), "../source_data/solutions/data/")
  out_dir = join(dirname(__file__), "data")
  file = join(out_dir, "pii_adversarial.json")
  data = getData(source_dir)
  print(Fore.YELLOW + f"Total data length: {len(data)}" + Fore.WHITE)

  if not exists(file):
    with open(file, 'w') as pipe:
      pipe.write("[\n")
      """
      Open an array.
      """
      print(f"file created")
  else:
    compiled = json.loads(f"{open(file).read().replace("\n", "")[:-1]}]")
    compiled = [c.get("pid", 0) for c in compiled]
    data = [d for d in data if d.get("pad_id", 0) not in compiled]
    print(Fore.YELLOW + f"Unprocessed data length: {len(data)}" + Fore.WHITE)

  if len(data) > 0:
    for i, d in enumerate(data):
      data_keys = getPIID(d)
      piid, conversation = getPIID(d, data_keys=data_keys)
      pid = piid["pid"]
      pii = piid["pii"]
      r = piid["reasoning"]
      transcript = piid["transcript"]
      
      _conversation = [
        { "role": "user", "content": f"OUTPUT: ```{json.dumps(pii)}```\n\nREASONING:```{r}```" },
      ]
      checked, _conversation = checker(_conversation, stream_output=True, transcript=transcript)
      
      i = 0

      while checked["evaluation"] == False:
        conversation.append({"role": "assistant", "content": json.dumps(pii)})
        conversation.append({"role": "user", "content": f"{checked["reasoning"]} Try again."})
        # print(conversation)
        piid, conversation = _01_agent.LLM(conversation, stream_output=True)
        pii = piid["list"]
        r = piid["reasoning"]

        i += 1
        if i > 3:
          break
        else:
          _conversation.append({ "role": "assistant", "content": json.dumps(checked) })
          _conversation.append({ "role": "user", "content": f"OUTPUT: ```{json.dumps(pii)}```\n\nREASONING:```{r}```" })
          checked, _conversation = checker(_conversation, stream_output=True)
          # print(checked)


      with open(file, 'a') as pipe:
        if i != len(data)-1:
          pipe.write(f"{json.dumps({"pid": pid, "pii": pii})},\n")
        else:
          pipe.write(f"{json.dumps({"pid": pid, "pii": pii})}\n")
        print(f"file updated")

    with open(file, 'a') as pipe:
      pipe.write("]")
      """
      Close the array.
      """
      print(f"file created")



