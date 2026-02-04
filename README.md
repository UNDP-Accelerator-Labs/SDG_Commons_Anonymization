# SDG Commons Anonymization

Here is a procedure and associated scripts for anonymizing the content in the SDG Commons.
Note the following instructions should work on MacOS and Linux. They will need to be adapted for MS Windows.

## Step 0: Install the requirements

Create a ```python``` virtual environment by running the following command in a terminal window:
```
python -m venv {the_name_of_your_virtual_env}
```
Then activate the virtual environment by running:
```
source {the_name_of_your_virtual_env}/bin/activate
```
Finally, install all the requirements listed in the ```requirements.txt``` file by running:
```
pip install -r requirements.txt
```

## Step 1: Pull the data

To pull the data, first set up the environment variables in ```template.env```.
It is encouraged to save it to a new name in your environment.

Once you have added the relevant variables, source them by running:
```
source {your_template_filename}.env
```
If you do not have an SDG Commons API Key, go to [sdg-innovation-commons.org](https://sdg-innovation-commons.org/), log in to your account or create a new one, copy your API key at the bottom of the home page, and explore the docs for further information.

When you have sourced all the variables, run the ```source_data``` module:
```
python source_data
```
By default, this will pull data from the solutions catalogue ("What we See" on the SDG Commons), and store it in the sub-directory ```source_data/{source_catalogue_solutions_by_default}/data/```.
You can change the source catalogue by replacing the ```platform``` variable in ```source_data/__main__py```. 

## Step 2: Run the anonymization script

This step calls upon two AI agents who iteratively try to improve an output. Concretely, one agent tries to find the personal names in a given snippet of text, and the other validates the output and provides feedback. The two can converse up to 3 times by default. This upper limit is set in order not to get stuck in endless back and forths between the two agents, who have limited context windows.

The agents pull the data from the ```source_data/{source_catalogue_solutions_by_default}/data/``` directory that was created in the previous step, and iteratively process each file (a pad in the original data).

The agents rely on ```ollama``` and ```llama3.1:8b``` by default. If you wish to change the model, the easiest way is to edit the ```model``` variable in the ```chat``` function in ```anonymize/utils.py```.

To trigger the AI agents, simply run:
```
python anonymize
```

The output is a single ```json``` file written to ```anonymize/data``` that contains the ```id``` of each ```pad``` and a list of personal names. Note the output is updated each time the agents have finished "arguing" about a given file. It is only a proper ```json``` format once all the data has been processed. If you interupt the process, you must add a closing square bracket (```]```) at the end of the file.

## Step 3: Insert the data

This step connects to the SDG Commons database (preferably a dev or staging version); creates new ```sections_anonymized (jsonb)``` and ```anonymized (BOOLEAN)``` columns in the ```pads``` table; and add all the anonymized versions of the pads. In cases where pads do not contain content that needs to be anonymized, the structure is simply copied from ```sections``` to ```sections_anonymized``` to facilitated queries in the final application.

Ideally, the SDG Commons database should have been consolidated prior to this, following the procedure [here](https://github.com/UNDP-Accelerator-Labs/SDG_Commons_DB_consolidation).