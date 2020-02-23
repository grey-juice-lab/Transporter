import yaml
import os
import logging
from Rule import Rule


class Ruleset:
    def __init__(self, the_path, logger=None):
        self._rules_list = []
        self.logger = logger or logging.getLogger(__name__)

        for file in os.listdir(the_path):
            self.logger.info("Loading {} configuration file".format(file))
            self.load_file(os.path.join(the_path, file))
        print("{} rules loaded".format(len(self.rules)))

    def load_file(self, the_file):
        with open(the_file, "r") as fh:
            the_object = yaml.full_load(fh)
            for rule in the_object['rules']:
                self.logger.info("loading {}".format(rule['id']))
                self.rules.append(Rule(rule))

    def check_rules(self, txt):
        self.logger.debug("checking rules with file {}".format(txt))
        for rule in self.rules:
            res = rule.check_rule(txt)
            if res:
                self.logger.info("rule {} match!".format(rule.id))
                return res, rule.id
        self.logger.debug("no rule match")
        return False, False

    @property
    def rules(self):
        return self._rules_list

    def __repr__(self):
        return "\n".join([str(x) for x in self.rules])

