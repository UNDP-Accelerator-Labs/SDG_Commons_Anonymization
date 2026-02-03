import urllib.request
from pprint import pprint
import json
from os.path import join, exists, dirname
from os import makedirs, getenv

if __name__ == "__main__":
  token = getenv("API_KEY")
  platform = "solutions"

  contents = urllib.request.urlopen(f"https://{platform}.sdg-innovation-commons.org/apis/fetch/pads?output=json&token={token}&status=2&status=3&include_data=true&include_tags=true&include_metafields=true&include_locations=true&include_imgs=true").read()
  ## TO DO: UPDATE THIS ENDPOINT TO THE NEW SDG Commons URL

  for entry in json.loads(contents):
    out_dirname = join(dirname(__file__), f"{platform}/data")
    if not exists(out_dirname):
      makedirs(out_dirname)

    file = join(out_dirname, f"pad-{entry["pad_id"]}.json")

    if not exists(file):
      with open(file, "w") as pipe:
        pipe.write(json.dumps(entry))
        print(f"{entry["pad_id"]} file written")