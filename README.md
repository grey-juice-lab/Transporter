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
          
        - id: "rule_testing"
          description: "first test to moving"
          from: "file://var/gjl/test/{client}/4.Content_Delivered/{path}/{code}_{encoding}_{rest}.{ext}"
          to: "s3://gjl-client-backup/{client}/{encoding}/{code}_{encoding2}_{rest}.NEW"
          glacier: false
          no_match_vars:
              code: "_"
              encoding: "_"
              rest: "."


### Points to have into account: 
#### Variables: 
They allow define part of the "from" expression to reuse into the "to" one.

**Important**:

Into the "to" expression, you cannot duplicate variables. If you do that, a rule creation error will be raised.
Instead of that, you have to add a counter to the variable you want to duplicate. Check the case:

to: "s3://gjl-client-backup/{client}/{**encoding**}/{code}_{**encoding2**}_{rest}.NEW"

#### Glacier

this attribute indicates if we want to move the file directly to the glacier. 

#### no_match_vars

Sometimes there are some ambiguity into the filenames that makes difficult to understand which part belongs to one variable or not. 

For example, if we check this expression: 

{code}_{encoding2}_{rest}.txt 

If encoding2 has a "_" inside, it will frame the parser. Is to avoid that that no_match_vars attribute comes in.
This hash list points, for every variable we define, what characters will not be contained on it. That helps the parser to 
pick the right decisions.


 





