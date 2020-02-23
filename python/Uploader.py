#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
import logging

import mimetypes
import os
import sys
import threading

import boto3
from boto3.s3.transfer import TransferConfig


class ProgressPercentage(object):
    """
    This class helps to give info about the state of the upload
    """
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            if percentage % 1 == 0:
                sys.stdout.write(
                    "\r%s  %s / %s  (%.2f%%)" % (
                        self._filename, self._seen_so_far, self._size,
                        percentage))
                sys.stdout.flush()


class Uploader:
    def __init__(self, the_bucket, concurrency=4, megas=8, just_s3=True):
        self._bucket = the_bucket
        self.concurrency = concurrency
        self.megas = megas
        self.just_s3 = just_s3

    def multi_part_upload_with_s3(self, file_path, key_path):
        s3 = boto3.resource('s3')
        config = TransferConfig(multipart_threshold=int(self.megas * 1024 * 1024),
                                max_concurrency=int(self.concurrency),
                                multipart_chunksize=int(self.megas * 1024 * 1024),
                                use_threads=True)

        mime_type = mimetypes.guess_type(file_path)[0]
        logging.info("Uploader: File is {}".format(mime_type))

        ExtraArgs = {'ACL': 'private'}
        if not self.just_s3:
            ExtraArgs['StorageClass']='GLACIER'
        if mime_type:
            ExtraArgs['ContentType'] = mime_type

        s3.meta.client.upload_file(file_path, self._bucket, key_path,
                                   ExtraArgs=ExtraArgs,
                                   Config=config,
                                   Callback=ProgressPercentage(file_path)
                                   )
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="this scripts uploads large files to S3")
    parser.add_argument("-concurrency", help="concurrency", default=10)
    parser.add_argument("-megas", help="chunks (and minimum size to multipart upload", default=8)
    parser.add_argument("origin", help="path to the origin file")
    parser.add_argument("destination", help="key for the file on S3 bucket")

    arguments = parser.parse_args()
    up = Uploader(the_bucket="gjl-test-upload")

    print("begin upload of {} to {}".format(arguments.origin, arguments.destination))
    start = time.time()
    up.multi_part_upload_with_s3(arguments.origin,
                                 arguments.destination,
                                 arguments.concurrency,
                                 arguments.megas,
                                 to_glacier=True)
    end = time.time()
    print("done on {} seconds".format(end - start))
