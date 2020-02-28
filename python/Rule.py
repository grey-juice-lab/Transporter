#!/usr/bin/env python
import re
import logging
import argparse

PROTOCOL = re.compile(r"^([^:]+):/")
GET_VARS = re.compile(r"{([^}]+)}")
DUP_VAR = re.compile(r"([^\d]+?)(\d*)$")
STARTING_PATH = re.compile(r"^[^:]+:/(/[^{]+){")
PARSE_VAR = "(?P<{}>[^/]+)"
PARSE_NO_VAR = "(?P<{}>[^/{}]+)"
ALLOWED_PROVIDERS = ["file", "s3"]


class Uri:
    """ This class manages the conversion from human readable from/to strings
        to the regular expressions that helps to recover the data
    """
    def __init__(self, uri_str, no_match_vars={}, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.uri_str = uri_str
        self.vars = GET_VARS.findall(uri_str)
        self.protocol = self.get_protocol()
        self.basepath = self.get_basepath()
        self.no_match_vars = no_match_vars
        uri_path = PROTOCOL.split(uri_str)[2]

        parts = GET_VARS.split(uri_path)                             # recover the variables into the URL
        new_re = "".join([self._subs_var(x) for x in parts]) + "$"   # substitute the vars for re groups
        self.uri_re = re.compile(new_re)
        self.logger.info(self.uri_re)

    def __repr__(self):
        return "URI:{}".format(self.uri_str)

    def _subs_var(self, part):
        if part in self.vars:
            stuffed = self.no_match_vars.get(part, "")
            if not stuffed:
                return PARSE_VAR.format(part)
            else:
                return PARSE_NO_VAR.format(part, stuffed)
        else:
            return part

    def matches(self, text):
        self.logger.debug("checking: {}".format(text))
        result = self.uri_re.match(text)
        if result:
            self.logger.debug("Uri {} Match!".format(self.uri_str))
            return dict(zip(self.vars, result.groups()))
        else:
            self.logger.debug("Uri {} Not Match".format(self.uri_str))
            return {}

    def replace(self, value_vars):
        def check_replica(key):
            check = DUP_VAR.match(key)
            return check.groups()[0]

        output_format = self.uri_str
        output_vars = GET_VARS.findall(self.uri_str)
        for key in output_vars:                         # check the vars into the to: string
            replaced_var = check_replica(key)           # replace var<num> per var
            if replaced_var in self.vars:               # FIXME: case no var<empty>, must be validate
                output_format = output_format.replace(r"{{{}}}".format(key), value_vars.get(replaced_var))
        if "{" not in output_format:
            self.logger.debug("Uri {} replaced to {}".format(self.uri_str, output_format))
            return output_format
        else:
            raise Exception("Error happened with {} values:{}".format(self.uri_str, str(value_vars)))

    def get_basepath(self):
        res = STARTING_PATH.findall(self.uri_str)
        if res:
            return res[0]
        else:
            return ""

    def get_protocol(self):
        res = PROTOCOL.findall(self.uri_str)
        if res:
            protocol = res[0]
            if protocol in ALLOWED_PROVIDERS:
                return protocol
            else:
                raise Exception("Unrecognized protocol: {}".format(protocol))
        else:
            raise Exception("No protocol on the uri: {}".format(self.uri_str))


class Rule:
    """ This class manages the Rule objects and their actions. Uses Uri Class to manage the endpoints
        properly.
        It processes the YAML rule objects obtained directly from the configuration files.
    """
    def __init__(self, rule, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        try:
            self.id = rule['id']
            self.description = rule.get('description', '')
            self.from_str = rule['from']
            self.from_provider = Rule.get_provider(rule['from'])
            self.from_basepath = Rule.get_starting_path(rule['from'])
            self.from_start_search = Rule.get_starting_path(self.from_str)
            self.to_str = rule['to']
            self.to_provider = Rule.get_provider(rule['to'])
            self.no_match_vars = rule.get('no_match_vars', {})
            self.from_uri = Uri(self.from_str, self.no_match_vars)
            self.to_uri = Uri(self.to_str, {})  # we do not pass no_match_vars because its pointless
            self.glacier = rule.get('glacier', False)
            # Not implemented self.delete_after = rule.get('delete_after', True)
            self.logger.info("loaded Rule {}".format(self))
        except:
            self.logger.error("malformed rule {}".format(rule.get('id', 'unknown')), exc_info=True)
            raise Exception("malformed rule {}".format(rule.get('id', 'unknown')))

    def __repr__(self):
        return "{}:{}\nfrom {} to {}\n".format(self.id, self.description, self.from_uri, self.to_uri)

    @classmethod
    def get_provider(cls, uri_str):
        res = PROTOCOL.findall(uri_str)
        if res:
            protocol = res[0]
            if protocol in ALLOWED_PROVIDERS:
                return protocol
            else:
                raise Exception("Unrecognized protocol: {}".format(protocol))
        else:
            raise Exception("No protocol on the uri: {}".format(uri_str))

    @classmethod
    def get_starting_path(cls, uri_str):
        res = STARTING_PATH.findall(uri_str)
        if res:
            return res[0]
        else:
            return ""

    def check_rule(self, text):
        self.logger.debug("checking rule {} with {}".format(self, text))
        kv = self.from_uri.matches(text)
        if kv:
            self.logger.debug("RuleMatch: {} with: {}".format(text, self))
            return self.to_uri.replace(kv)
        else:
            self.logger.debug("RuleFail: {} with: {}".format(text, self))
            return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="This script allow check  filenames")
    parser.add_argument("the_expression", help="expression with ")
    parser.add_argument("-dryrun", help="just checks what it will do", action="store_true")

    args = parser.parse_args()