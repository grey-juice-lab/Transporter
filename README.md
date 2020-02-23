# transporter
project to move file among devices/cloud

## How to install it
You must have a python 3.7 installed on your system.
The steps to install are the following ones:

    cd <transporter path>
    python3 -mvenv .venv
    source .venv/bin/activate
    pip install -r requirements.txt


## How to use it
Below, there is a example of call of transporter:

    cd transporter
    source .venv/bin/activate
    python transporter <path to rules folder> [-dryrun]

where:
* **path to rules folder**: is the path to a folder full of rules.yaml files
* **-dryrun**: just for checking the actions transporter will make

## The rules file
Transporter works becase there are rules that must follow. This rules are gathered into a folder, in one or more files.
The rules file is a simple YAML file where rules are a list of dictionaries.
A sample of rule can be showed below:

    ---
    rules:
        - id: "rule_1"
          description: first rule. Does something
          from: "file://Users/manel/work/origin/{CLIENT}/output_path/{FILE}
          to: "file://output/{CLIENT}/{FILE}
          glacier: false

        - id: "rule_2"
          description: first rule. Does something
          from: "file://Users/manel/work/origin/{CLIENT}/output_path/{FILE}
          to: "s3://bucket_backup/{CLIENT}/{FILE}
          glacier: true
