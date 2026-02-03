"""
This script is for extracting entity names from a prompt.
"""
from colorama import Fore # this is to colorize the terminal output

import json
import re
from sys import path as syspath
from os.path import dirname, join

syspath.append(dirname(__file__))
from utils import chat, rmURL

def checker(conversation:list, **kwargs) -> list[str]:
  transcript = kwargs.get("transcript", None)
  if next((c for c in conversation if c.get("role", None) == "system"), None) is None and transcript is not None:
    SYSPROMPT = f"""You are an AI agent that communicates directly with another AI agent.
    You are responsible for checking the OUTPUT of the other AI agent. 
    You are given the OUTPUT of the other AI agent and its REASONING.

    The other AI agent is a legal specialist responsible for flagging personal names, and only personal names, in the following TRANSCRIPT:

    ```
    {transcript}
    ```

    The OUPUT of the other AI agent should be a list containing only personal names — no pronouns, descriptive adjectives, company names, organization names or location names.
    Note that if the TRANSCRIPT contains no personal names, the OUTPUT should be an empty list.

    Your role is to compare the OUTPUT with the TRANSCRIPT to determine whether the other AI agent has extracted all the personal names from the TRANSCRIPT.

    You return a json object, and only the json object, with a boolean value for your evaluation of whether the other AI agent has extracted all personal, and only the personal names in the TRANSCRIPT, and a string providing a reason for your assessment.
    The json object should look like this:

    {{
      "evaluation": true if the other AI agent correctly successfully extracted all the personal names, and only the personal names in the TRANSCRIPT or if there are no personal names in the TRANSCRIPT | false if otherwise,
      "reasoning": an explanation for your assessment, including all the areas where the other AI agent was right, and where it was wrong. Do not make generic statements like "you missed the personal names in the TRANSCRIPT". Be specific. This message is adresed to the other AI agent so it can improve its response.
    }}

    The json object should be valid json, and not surrounded by quotes as it needs to be parsed immediately in python.
    You address the AI agent in the "reasoning" field using second-person pronouns."""
    conversation.insert(0, { "role": "system", "content": SYSPROMPT })

  full_response = chat(
    conversation=conversation,
    output_format='json',
    **kwargs
  )
  try:
    data = json.loads(full_response)
    return (data, conversation)
  except:
    return ({"evaluation": False, "reasoning": full_response, "failed": True}, conversation)

if __name__ == '__main__':
  in_file = join(dirname(__file__), "data/pii_info_a1.json")
  data = json.loads(f"{open(in_file).read().replace("\n", "")}")
  data = [
    d for d in data 
    if d.get("pii", None) is not None 
    and len(rmURL(d.get("pii", []))) > 0
  ]

  for i, d in enumerate(data):
    pid = d.get("pid", 0)
    pii = d.get("pii", [])
    transcript = d.get("transcript", "")

    print(pii)
    checked = checker(transcript, pii, stream_output=True)
    print(checked)