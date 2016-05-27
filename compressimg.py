# -*- coding: utf-8 -*-

import argparse
import os
import time
from shutil import copytree
from multiprocessing import Pool

import tinify

import config


VALID_EXTENSIONS = ('.jpeg', '.jpg', '.png')


def log(message):
    print(message)


def convert(image_file):
    done = False
    message = ''

    try:
        log('Compressing {} ...'.format(image_file))
        source_file = tinify.from_file(image_file)
        source_file.to_file(image_file)

    except tinify.AccountError:
        message = 'ERROR: Verify your API key and your account limit.'

    except tinify.ClientError:
        message = 'ERROR: Problem with your request options or your image.'

    except tinify.ServerError:
        message = 'ERROR: Temporary issue on Tinify API.'

    except tinify.ConnectionError:
        message = 'ERROR: Network connection problem.'

    except Exception:
        message = 'ERROR: Something goes wrong and I do not know why.'
    else:
        done = True

    return done, message


def get_convertible_files(directory):
    convertible_files = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            get_convertible_files(entry.path)

        _, extension = os.path.splitext(entry.path)
        if extension.lower() not in VALID_EXTENSIONS:
            continue

        convertible_files.append(entry.path)

    return convertible_files


def convert_files(image_file):
    done = False
    time_to_retry = 10  # seconds
    retries = 10

    while retries:
        done, message = convert(image_file)
        if done:
            break

        message += ' Time to retry: {}'.format(time_to_retry)
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

    pool = Pool(processes=4)
    pool.map(convert_files, get_convertible_files(directory))
