from os import listdir
from os.path import join, dirname, isfile, exists
import json
from sys import path as syspath
from pprint import pprint
import re

from itertools import permutations

from colorama import Fore # this is to colorize the terminal output

syspath.append(dirname(__file__))
from utils import getData, getContactDetails, psqlTable

def redact(txt:str,pii:list) -> str:
  txt = txt.replace("\xa0", " ")
  txt = re.sub(r"\s+", " ", txt)
  contactDetails = getContactDetails(txt)

  for p in pii:
    if re.search(p, txt, flags=re.IGNORECASE):
      txt = re.sub(p, "[REDACTED]", txt, flags=re.IGNORECASE)
    else:
      ## Check for permutations
      if len(p.split(" ")) > 1:
        _p = p.split(" ")
        perms = permutations(_p)
        for perm in perms:
          txt = re.sub(" ".join(perm), "[REDACTED]", txt, flags=re.IGNORECASE)

  if len(contactDetails) > 0:
    for c in contactDetails:
      txt = re.sub(re.escape(c), "[REDACTED]", txt, flags=re.IGNORECASE)
  return txt

def traverseStructure(data:dict,pii:list) -> dict:
  pid = data.get("pad_id", None)
  iso3 = data.get("iso3", "NUL")
  date = data.get("created_at", None)
  # print(iso3, date, pid)
  sections = data.get("sections", [])

  for s in sections:
    title = s.get("title", None)
    if title is not None:
      s["title"] = redact(title, pii)

    items = s.get("items", [])
    
    if len(items) == 1 and items[0].get("type", "").lower() == 'group':
      i = items[0]
      sub_item_list = i.get("items", [])

      for sub_items in sub_item_list:
        print("sublist")
        # print(sub_items)
        # TO DO
        pass
    else:
      for i in items:
        txt = i.get("txt", None)
        if txt is not None: 
          i["txt"] = redact(txt, pii)
        
  full_txt = "\n".join([i.get("txt", None) for s in sections for i in s.get("items",[]) if i.get("txt", None) is not None])
  all_titles = "\n".join([s.get("title", None) for s in sections if s.get("title", None) is not None])
  if "[REDACTED]" not in full_txt and "[REDACTED]" not in all_titles:
    print("issue here")
    print(pid, pii)
    print("\n")

  return sections
  
if __name__ == "__main__":
  ## Establish DB connection
  conn = psqlTable("sdg_commons_master_202601")
  ## Create the redacted sections column if it does not exist, as well as a redacted flag columns
  conn.execute("ALTER TABLE pads ADD COLUMN IF NOT EXISTS sections_redacted jsonb;")
  conn.execute("ALTER TABLE pads ADD COLUMN IF NOT EXISTS redacted BOOLEAN DEFAULT FALSE")
  ## Reset the redacted sections column
  conn.execute(f"UPDATE pads SET sections_redacted = sections")
  ## Get the data
  ## This should be up to date, since it is pulling from the prod API, not the DB
  source_dir = join(dirname(__file__), "../source_data/solutions/data/")
  data = getData(source_dir)
  ## Get the anonymzation information
  piis = json.loads(open(join(dirname(__file__), "../anonymize/data/pii_adversarial.json")).read())
  piis = [d for d in piis if len(d.get("pii",[])) > 0]
  piis_pids = [d.get("pid", None) for d in piis if d.get("pid", None) is not None]
  
  data = [d for d in data if d.get("pad_id", None) in piis_pids]

  for i, d in enumerate(data):
    pid = d.get("pad_id", None)
    pii_pid = next((d for d in piis if d.get("pid", None) == pid), None)
    pii = pii_pid.get("pii", [])
    ## Remove Maarten Grootendorst
    rm = ["Maarten Grootendorst","Maarten","Grootendorst"]
    pii = [p for p in pii if p not in rm]
    ## Sort the pii to have the longest first, in case first and last name are separated
    pii.sort(key=len,reverse=True)
    
    if len(pii) > 0:
      redacted_sections = traverseStructure(d, pii)
     
      if "[REDACTED]" in json.dumps(redacted_sections):
        ## Store everything in the DB
        conn.execute(f"UPDATE pads SET sections_redacted = %s::jsonb WHERE id = %s AND ordb = %s", (json.dumps(redacted_sections), pid, 4))
        conn.execute(f"UPDATE pads SET redacted = TRUE WHERE id = %s AND ordb = %s", (pid, 4))
        print(f"{pid} updated")

  conn.close()
