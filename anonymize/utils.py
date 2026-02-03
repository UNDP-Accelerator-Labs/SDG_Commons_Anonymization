from os import listdir
from os.path import join, isfile
import json
import re

from colorama import Fore # this is to colorize the terminal output

from ollama import chat as ollama_chat
import readline

def chat(conversation,**kwargs) -> dict:
  stream_output = kwargs.get("stream_output", False)
  model = kwargs.get("model", "llama3.1:8b")
  options = kwargs.get("options", {
    'seed': 42,
    'temperature': 0,
    'num_ctx': 4000,
  })
  output_format = kwargs.get("format", None)

  stream = ollama_chat(
    messages=conversation,
    model=model, 
    options=options,
    format=output_format,
    stream=stream_output,
  )

  full_response = ''

  if stream_output == True:
    print(Fore.YELLOW + "using AI" + Fore.WHITE)
    for chunk in stream:
      print(Fore.YELLOW + chunk['message']['content'] + Fore.WHITE, end='', flush=True)
      full_response += chunk['message']['content']
    print('\n')
  else:
    full_response = stream['message']['content']

  return full_response


def editableInput(prompt, initial=''):
  """
  Credit to https://github.com/python/cpython/issues/81342
  """
  readline.set_startup_hook(lambda: readline.insert_text(initial))
  try:
    response = input(prompt)
  finally:
    readline.set_startup_hook(None)
  return response

def getData(source_dir):
  data = []
  for f in listdir(source_dir):
    if isfile(join(source_dir, f)) and f != '.DS_Store':
      data.append(json.loads(open(join(source_dir, f)).read()))
  return data

def getPartnerType(instruction):
  if instruction == "If applicable, what private sector partners did you actually work with and what did you do with them?":
    return "private sector"
  elif instruction == "If applicable, what academic partners (and related institutions) did you actually work with and what did you do with them?":
    return "academia"
  elif instruction == "If applicable, what government partners (and related institutions) did you actually work with and what did you do with them?":
    return "government"
  elif instruction == "If applicable, which UN internal partners did you actually work with and what did you do with them?":
    return "UN"
  elif instruction == "If applicable, what civil society organisations did you actually work with and what did you do with them?":
    return "civil society"
  elif instruction == "Relating to your answers above: who of the partners listed were new and unusual partners for UNDP, and what made them special?":
    return "unusual partner"
  else:
    return None

def rmURL(data:list) -> list[str]:
  exp = r"^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$"
  return [d for d in data if not re.match(exp, d)]