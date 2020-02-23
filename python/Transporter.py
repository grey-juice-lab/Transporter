#!/usr/bin/env python

from os import stat
from time import sleep
import argparse
import logging
from logging.config import fileConfig
from RuleSet import Ruleset
from Mover import Mover
from Notifier import *


class Movement:
    def __init__(self, origin, destination, rule):
        self.origin = origin
        self.destination = destination
        self.origin_size = stat(self.origin).st_size
        self.rule = rule
        self.status = "init"
        self.changed = False

    def compare_size(self):
        ret = stat(self.origin).st_size
        if ret != self.origin_size:
            self.changed = True
            return False
        return True

    def __repr__(self):
        return "{} -> {} ({}) changed:{} status:{}".format(self.origin,
                                                            self.destination,
                                                            self.rule.id,
                                                            self.changed,
                                                            self.status)


class Transporter:
    def __init__(self, the_path, logger=None, dryrun=False):
        self.logger = logger or logging.getLogger(__name__)
        self.rules_path = the_path
        self.rules_set = Ruleset(the_path)
        self.mover = Mover("fakeS3")
        self.dryrun = dryrun
        self.moving_files = []

    def check_changes(self, wait=2):
        self.logger.debug("waiting {} sec to check file sizes again".format(wait))
        sleep(wait)
        return all([x.compare_size() for x in self.moving_files])

    def run(self):
        if len(self.rules_set.rules) == 0:
            self.logger.info("No rules loaded. nothing to do")
            return False
        else:
            self.logger.info("Starting file collection...")
            for rule in self.rules_set.rules:
                self.logger.debug("checking rule {}".format(rule))
                if rule.from_provider == 'file':
                    for file in self.mover.file_get_by_prefix(rule.from_basepath):
                        self.logger.debug("checking file: {}".format(file))
                        new_file = rule.check_rule(file)
                        if new_file:
                            self.moving_files.append(Movement(file, new_file, rule))

            self.logger.info("there are {} actions to do:".format(len(self.moving_files)))
            if self.moving_files:
                res = self.check_changes()    # validate than no file has changed
                for count, mv in enumerate(self.moving_files):
                    self.logger.debug(mv)
                    if not mv.changed:
                        if mv.rule.to_provider == 'file':
                            self.mover.copy_files(mv, self.dryrun)
                        if mv.rule.to_provider == 's3':
                            self.mover.copy_to_s3(mv, self.dryrun)
                    else:
                        self.logger.debug("File {} has changed its size. skipping".format(mv.origin))
                        mv.status = "skipped"

                # once everything is copied, delete the originals
                self.mover.delete_files(self.moving_files, self.dryrun)
                return True
            else:
                return False

    def summary(self):
        if len(self.rules_set.rules) == 0:      # No rules found.
            if self.dryrun:
                self.logger.info("Transporter (DRYRUN) no Rules loaded. nothing to do")
            else:
                send_email(subject="Transporter: No rules loaded",
                          body="Transporter did nothing because there are no rules. "
                               "check the rules path: {} and try again".format(self.rules_path))
            return False

        if len(self.moving_files) == 0:       # No files found
            if self.dryrun:
                self.logger.info("Transporter (DRYRUN) no files found. Nothing to do")
            else:
                send_email(subject="Transporter: No files found",
                           body="Transporter did nothing because there are no files that match the current rules. "
                               "There are the current rules:\n{}".format(self.rules_set))
            return False

        # there are moves on the list:
        files_moved = len([x for x in self.moving_files if x.status == "moved"])
        files_ko = len(self.moving_files) - files_moved
        movements = "\n".join([str(x) for x in self.moving_files])
        body = "There is the list of movements and their status:\n{}".format(movements)

        if self.dryrun:
            self.logger.info("Transporter (DRYRUN): {} movements".format(len(self.moving_files)))
            self.logger.info(body)
        else:
            subject = "Transporter: {} Files moved, {} Files with problems".format(files_moved, files_ko)
            send_email(subject, body)
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="This script moves files following a set or rules")
    parser.add_argument("rules_path", help="path where the rules are")
    parser.add_argument("-dryrun", help="just checks what it will do", action="store_true")

    args = parser.parse_args()
    fileConfig('logging_config.ini')
    logger = logging.getLogger()

    tr = Transporter(args.rules_path, logger, args.dryrun)
    try:
        tr.run()
        tr.summary()
    except Exception as e:
        logger.error("Some error comes up with the execution:", exc_info=True)
        send_email(subject="Transporter: some error happened running it ", body=e)
