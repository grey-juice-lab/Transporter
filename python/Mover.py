import Uploader
import os
import shutil
import re
import logging

# upload configuration
CONCURRENCY = 2
MEGAS = 8

# regular expressions for URIS
file_expr = re.compile("file://([^/]+)(/.*)")
PROTOCOL = re.compile(r"^([^:]+):/")
s3_expr = re.compile("s3://([^/]+)/(.*)")


def split_uri(prefix):
    res = PROTOCOL.split(prefix)
    if res and len(res):
        return res[1], res[2]
    else:
        return "", ""


def split_bucket(prefix):
    res = s3_expr.findall(prefix)
    if res and len(res):
        return res[0][0], res[0][1]
    else:
        return "", ""


class Mover:
    def __init__(self, s3=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.s3 = s3

    def file_get_by_prefix(self, prefix):
        self.logger.debug("prefix is: {}".format(prefix))
        path, pattern = os.path.split(prefix)
        for (dirpath, dirnames, filenames) in os.walk(path):
            for file in filenames:
                yield os.path.join(dirpath, file)

    def s3_get_by_prefix(self, prefix):
        if not self.s3:
            self.logger.error("No AWS initialization has been done. Aborting")
            raise Exception("No AWS initialization was done")

        the_bucket, the_prefix = split_bucket(prefix)
        if the_bucket:
            ret = self.s3.list_objects_v2(Bucket=the_bucket, Prefix=the_prefix)
            for file in ret['Contents']:
                yield file['Key']
            while ret['IsTruncated']:
                ret = self.s3.list_objects_v2(Bucket=the_bucket,
                                              Prefix=the_prefix,
                                              ContinuationToken=ret['NextContinuationToken'])
                for file in ret['Contents']:
                    yield file['Key']

    def copy_to_s3(self, mv, dryrun=False):
        the_file = mv.origin
        end_s3_file = mv.destination
        self.logger.info("S3Mover{}: Uploading {} to {}".format(dryrun and "DRYRUN" or "", the_file, end_s3_file))
        the_bucket, the_prefix = split_bucket(end_s3_file)
        self.logger.info("destination: {} bucket: {} prefix: {}".format(end_s3_file, the_bucket, the_prefix))

        if dryrun:
            return True

        if the_bucket:
            up = Uploader.Uploader(the_bucket=the_bucket,
                                   concurrency=CONCURRENCY,
                                   megas=MEGAS,
                                   just_s3=not mv.rule.glacier)
            try:
                ok_upload = up.multi_part_upload_with_s3(the_file, the_prefix)
                self.logger.info("copy_to_s3: File {} was uploaded successfully".format(the_file))
                mv.status = "copied"
                return True
            except Exception as e:
                self.logger.error("copy_to_s3: There was an error uploading {}. {}".format(the_file, e))
                return False
        else:
            self.logger.error("copy_to_s3: There is not bucked defined: {}".format(end_s3_file))
            return False

    def copy_files(self, mv, dryrun=False):
        origin_file = mv.origin
        end_file = mv.destination
        _, the_end_file = split_uri(end_file)
        self.logger.info("copy_files{}: moving {} to {}".format(dryrun and "DRYRUN" or "", origin_file, the_end_file))
        if not dryrun:
            try:
                shutil.copy(origin_file, the_end_file)
                mv.status = "copied"
                return True
            except:
                self.logger.error("copy_files: error copying {} to {}".format(origin_file, the_end_file),
                                  exc_info=True)
                return False

        return True

    def delete_files(self, the_list_mv, dryrun=False):
        def check_delete_safe(current_mv):
            # case 1: more movements of the same origin file
            possibles = [x for x in the_list_mv if current_mv.origin == x.origin and current_mv != x]
            if not possibles:
                return current_mv.status == 'copied'   # just 1 case. its fine delete if already copied

            # case 2: there are more movements same origin file. checking status of all them is copied
            pending = [x for x in possibles if x.status not in ["copied", "moved"]]
            if pending and len(pending) != 0:
                return False
            # all good
            return current_mv.status == 'copied'  # other cases are OK. if me am not still copied, cannot delete

        for mv in the_list_mv:
            self.logger.info("FileDeleter{}: Deleting {}".format(dryrun and "DRYRUN" or "", mv.origin))
            if dryrun:
                continue

            # check multiple destination in case of same origin or whether the status is copied
            if check_delete_safe(mv):
                try:
                    os.unlink(mv.origin)
                    mv.status = "moved"
                except FileNotFoundError:
                    mv.status = "moved"  # already deleted
                except:
                    self.logger.error("delete_files: error deleting {}".format(mv.origin), exc_info=True)
            else:
                self.logger.warning("Cannot delete the file {} status {}. "
                                 "Check status or dependences (same file origin "
                                 "failed to copy in other movement?)".format(mv.origin, mv.status))
