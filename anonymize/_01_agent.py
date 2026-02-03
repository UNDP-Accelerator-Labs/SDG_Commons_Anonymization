"""
This script is for extracting entity names from a prompt.
"""
from colorama import Fore # this is to colorize the terminal output

import json
import re
from sys import path as syspath
from os.path import dirname, join
from pprint import pprint

syspath.append(dirname(__file__))
from utils import chat

SYSPROMPT = """You are a legal specialist concerned with the leaking of personal identifiable information (PII).
You are given a TEXT TRANSCRIPT to scan for all personal names, and only personal names — no pronouns, descriptive adjectives, company names, organization names or location names.
When you find a personal name, add it to a list so that it can be removed from the TRANSCRIPT. 
Any information other than personal names is not relevant. If you do not find any personal names, simply return an empty list.
Do not split first and last names.

You return a json object, and only the json object, that looks like this:

{
  "list": all the personal names, and only the personal names extracted from the TRANSCRIPT,
  "reasoning": an explanation for your assessment, adressed directly to the user using second-person pronouns.
}

The json object should be valid json, and not surrounded by quotes or any other text, as it needs to be parsed immediately in python."""


# SYSPROMPT = """
# You are a legal specialist concerned with the leaking of personal identifiable information (PII).
# The user will ask you to scan a TEXT TRANSCRIPT to extract all personal names.
# If you find a personal name, return it in a python list. Do not split first and last names.
# You respond with the list and only the list, so that it can be parsed as json in python.
# Do not respond with any additional text.
# """


## TO DO: GIVE A REASON FOR THE RESPONSE TO SEND TO THE CHECKER AGENT

# SYSPROMPT = """
# You are an analyst who extracts personal identifiable information (PII) from a short text passed to you by the user.
# PII is information that can be used to distinguish or trace an individual’s identity,
# such as name, social security number, biometric data records—either alone or when combined with other 
# personal or identifying information that is linked or linkable to a specific individual 
# (e.g., date and place of birth, mother’s maiden name, etc.).
# """
# SYSPROMPT = """
# You are a legal specialist that is concerned with the leaking of personal identifiable information.
# Your goal is to identify names from a text TRANSCRIPT 
# so that they can be redacted to anonymize the TRANSCRIPT.
# You are given the TRANSCRIPT, and you return a python list, and only a python list.
# If you do not find any names, simply return an empty list.
# The list should look like this:

# ['name', 'name', 'etc']

# The list should not be surrounded by quotes as it needs to be parsed immediately in python.
# """

def LLM(conversation:list,**kwargs) -> dict[str]:
  if next((c for c in conversation if c.get("role", None) == "system"), None) is None:
    conversation.insert(0, { "role": "system", "content": SYSPROMPT })
  
  full_response = chat(
    conversation=conversation,
    output_format='json',
    **kwargs
  )
  try:
    data = json.loads(full_response)
    """
    Filter Maarten Grootendorst, the author of KeyBERT as this is a required accreditation.
    """
    # data = [d for d in data if d != "Maarten Grootendorst"]
    return (data, conversation)
  except:
    return ({"list": [], "reasoning": full_response, "failed": True}, conversation)

if __name__ == '__main__':
  while True:
    print(Fore.WHITE + 'USER:')
    prompt = input()
    main(prompt, stream_output=True)
