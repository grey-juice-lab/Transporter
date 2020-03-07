# Transporter
project to move file among filesystem to s3.


## How to install it
You must have a python 3.7 installed on your system.
The steps to install are the following ones:

    cd <transporter path>/python
    python3 -mvenv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## The rules file
Transporter works because there are rules that must follow. This rules are gathered into a folder, in one or more files.
The rules file is a simple YAML file where rules are a list of dictionaries.
A sample of rule can be showed below:

    ---
    rules:
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

{code}\_{encoding2}\_{rest}.txt 

If encoding2 has a "_" inside, it will frame the parser. Is to avoid that that no_match_vars attribute comes in.
This hash list points, for every variable we define, what characters will not be contained on it. That helps the parser to 
pick the right decisions.

### How to use it

Remember to use the virtualenv before calling the Python file: 

```shell script
cd <transporter>/python
source .venv/bin/activate
```

If you want to call it directy, just follow the next steps:

```shell script
python Transporter.py <rules> [-dryrun]
```
This will execute the rules engine (every rules must be into the ./rules path). If you want just to check what it is supposed this program to do, use the **-dryrun** parameter


You can just check if a file will match one of the rules, just call the program as follows: 
```shell script
python Transporter.py <rules> -checkfile <file with the full path> 
```
Here comes an example: 
```shell script
python Transporter.py rules -checkfile "/tmp/origin/CLIENTE1/4.results/fichero.txt"
2020-03-01 22:27:44,968 RuleSet      INFO     Loading rules0.yml configuration file
2020-03-01 22:27:44,971 RuleSet      INFO     loading zero_rule_test
2020-03-01 22:27:44,971 Rule         INFO     re.compile('/tmp/origin/(?P<client>[^/]+)/4.results/(?P<file>[^/.]+).(?P<ext>[^/.]+)$')
2020-03-01 22:27:44,972 Rule         INFO     re.compile('/gjl-client-backup/(?P<client>[^/]+)/(?P<file>[^/]+).new_extension_(?P<ext>[^/]+)$')
2020-03-01 22:27:44,972 Rule         INFO     loaded Rule zero_rule_test:move from a to b
from URI:file://tmp/origin/{client}/4.results/{file}.{ext} to URI:s3://gjl-client-backup/{client}/{file}.new_extension_{ext}

2020-03-01 22:27:44,972 RuleSet      INFO     Loading sample_conf.yml configuration file
2020-03-01 22:27:44,976 RuleSet      INFO     loading cl_p1
2020-03-01 22:27:44,977 Rule         INFO     re.compile('/Users/manel/work/transporter_samples/source/(?P<CLIENT>[^/]+)/path1/cl(?P<FILE>[^/]+)$')
2020-03-01 22:27:44,978 Rule         INFO     re.compile('/Users/manel/work/transporter_samples/destination/path1/(?P<CLIENT>[^/]+)/NEW_CLI(?P<FILE>[^/]+)$')
2020-03-01 22:27:44,978 Rule         INFO     loaded Rule cl_p1:move client data paht1
from URI:file://Users/manel/work/transporter_samples/source/{CLIENT}/path1/cl{FILE} to URI:file://Users/manel/work/transporter_samples/destination/path1/{CLIENT}/NEW_CLI{FILE}

2020-03-01 22:27:44,978 RuleSet      INFO     loading cl_p2
2020-03-01 22:27:44,979 Rule         INFO     re.compile('/Users/manel/work/transporter_samples/source/(?P<CLIENT>[^/]+)/path2/(?P<FILE>[^/]+)$')
2020-03-01 22:27:44,979 Rule         INFO     re.compile('/Users/manel/work/transporter_samples/destination/path2/(?P<CLIENT>[^/]+)/(?P<FILE>[^/]+)$')
2020-03-01 22:27:44,980 Rule         INFO     loaded Rule cl_p2:move client data path2
from URI:file://Users/manel/work/transporter_samples/source/{CLIENT}/path2/{FILE} to URI:file://Users/manel/work/transporter_samples/destination/path2/{CLIENT}/{FILE}

2020-03-01 22:27:44,980 RuleSet      INFO     loading cl_to_s3
2020-03-01 22:27:44,980 Rule         INFO     re.compile('/Users/manel/work/transporter_samples/source/(?P<CLIENT>[^/]+)/(?P<PATH>[^/]+)/cl(?P<FILE>[^/]+)$')
2020-03-01 22:27:44,981 Rule         INFO     re.compile('/gjl-client-backup/backup/THE_PATH_(?P<PATH>[^/]+)/(?P<CLIENT>[^/]+)/NEW_CLI(?P<FILE>[^/]+)$')
2020-03-01 22:27:44,981 Rule         INFO     loaded Rule cl_to_s3:move client data paht1
from URI:file://Users/manel/work/transporter_samples/source/{CLIENT}/{PATH}/cl{FILE} to URI:s3://gjl-client-backup/backup/THE_PATH_{PATH}/{CLIENT}/NEW_CLI{FILE}

2020-03-01 22:27:44,981 RuleSet      INFO     Loading rules1_test.yml configuration file
2020-03-01 22:27:44,985 RuleSet      INFO     loading rule_testing
2020-03-01 22:27:44,986 Rule         INFO     re.compile('/var/gjl/test/(?P<client>[^/]+)/4.Content_Delivered/(?P<path>[^/]+)/(?P<code>[^/_]+)_(?P<encoding>[^/_]+)_(?P<rest>[^/]+).(?P<ext>[^/.]+)$')
2020-03-01 22:27:44,986 Rule         INFO     re.compile('/gjl-client-backup/(?P<client>[^/]+)/(?P<encoding>[^/]+)/(?P<code>[^/]+)_(?P<encoding2>[^/]+)_(?P<rest>[^/]+).NEW$')
2020-03-01 22:27:44,987 Rule         INFO     loaded Rule rule_testing:first test to moving
from URI:file://var/gjl/test/{client}/4.Content_Delivered/{path}/{code}_{encoding}_{rest}.{ext} to URI:s3://gjl-client-backup/{client}/{encoding}/{code}_{encoding2}_{rest}.NEW

5 rules loaded
2020-03-01 22:27:44,987 root         INFO     checking file with the current rules
2020-03-01 22:27:44,987 root         INFO     checking rule zero_rule_test:move from a to b
from URI:file://tmp/origin/{client}/4.results/{file}.{ext} to URI:s3://gjl-client-backup/{client}/{file}.new_extension_{ext}

2020-03-01 22:27:44,987 root         INFO     File match with rule zero_rule_test
2020-03-01 22:27:44,987 root         INFO     Origin: /tmp/origin/CLIENTE1/4.results/fichero.txt
2020-03-01 22:27:44,987 root         INFO     Destination: s3://gjl-client-backup/CLIENTE1/fichero.new_extension_txt
```


 





