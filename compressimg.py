# -*- coding: utf-8 -*-

import argparse
import os
import time
from shutil import copytree

import tinify

import config


VALID_EXTENSIONS = ('.jpeg', '.jpg', '.png')


def log(message):
    print(message)


def compressimg(directory):
    for entry in os.scandir(directory):

        if entry.is_dir():
            compressimg(entry.path)

        _, extension = os.path.splitext(entry.path)
        if extension.lower() not in VALID_EXTENSIONS:
            continue

        done = False
        time_to_retry = 10  # seconds
        retries = 10

        while retries:
            try:
                log('Compressing {} ...'.format(entry.path))
                source_file = tinify.from_file(entry.path)
                source_file.to_file(entry.path)
                done = True
                break

            except tinify.AccountError:
                message = (
                    'ERROR: Verify your API key and your account limit. '
                    'Trying again in {} seconds'
                ).format(time_to_retry)

            except tinify.ClientError:
                message = (
                    'ERROR: Problem with your request options or your image. '
                    'Trying again in {} seconds'
                ).format(time_to_retry)

            except tinify.ServerError:
                message = (
                    'ERROR: Temporary issue on Tinify API. '
                    'Trying again in {} seconds'
                ).format(time_to_retry)

            except tinify.ConnectionError:
                message = 'ERROR: Network connection problem. Trying again in {} seconds'.format(
                    time_to_retry
                )
            except Exception:
                message = (
                    'ERROR: Something goes wrong and I do not know why. '
                    'Trying again in $time_to_retry seconds'
                ).format(time_to_retry)

            log(message)
            retries -= 1
            time.sleep(time_to_retry)

        if not done:
            log(' SKIPPED!')


def valid_directory(directory):
    if not os.path.exists(directory):
        raise Exception('Directory not found: {}'.format(directory))

    if not os.path.isdir(directory):
        raise Exception('Invalid directory: {}'.format(directory))

    return os.path.normpath(os.path.realpath(directory))


def backup_files(directory, backup_directory):
    copytree(directory, backup_directory)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compress images using TinyPNG')
    parser.add_argument(
        'directory', help='Directory which contains images to be compressed'
    )
    parser.add_argument(
        'backup_dir',
        help='Backup directory for original files'
    )

    args = parser.parse_args()

    try:
        tinify.key = config.TINYPNG_KEY
        tinify.validate()
    except tinify.Error:
        message = ('ERROR: Invalid/Expired Key: {}'.format(config.TINYPNG_KEY))
        raise Exception(message)

    directory = valid_directory(args.directory)
    backup_files(directory, args.backup_dir)
    compressimg(directory)
