import sys
import logging
from contextlib import contextmanager

import fs
import fs.path

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


PY2 = sys.version_info[0] == 2
LOG = logging.getLogger(__name__)

path_join = fs.path.join
path_splitext = fs.path.splitext


def log_fs_failure(function_in_this_module):
    def wrapper(*args, **kwds):
        try:
            return function_in_this_module(*args, **kwds)
        except fs.errors.CreateFailed:
            from moban import reporter

            message = "Failed to open %s" % args[0]
            LOG.debug(message)
            reporter.report_error_message(message)
            raise

    return wrapper


@log_fs_failure
@contextmanager
def open_fs(path):
    path = to_unicode(path)
    if is_zip_alike_url(path):
        zip_file, folder = url_split(path)
        the_fs = fs.open_fs(zip_file)
    else:
        the_fs = fs.open_fs(path)
    try:
        yield the_fs
    finally:
        the_fs.close()


@log_fs_failure
@contextmanager
def open_file(path):
    path = to_unicode(path)
    if is_zip_alike_url(path):
        zip_file, folder = url_split(path)
        the_fs = fs.open_fs(zip_file)
        f = the_fs.open(folder)
    else:
        dir_name = fs.path.dirname(path)
        the_file_name = fs.path.basename(path)
        the_fs = fs.open_fs(dir_name)
        f = the_fs.open(the_file_name)
    try:
        yield f
    finally:
        f.close()
        the_fs.close()


@log_fs_failure
@contextmanager
def open_binary_file(path):
    path = to_unicode(path)
    if is_zip_alike_url(path):
        zip_file, folder = url_split(path)
        the_fs = fs.open_fs(zip_file)
        f = the_fs.openbin(folder)
    else:
        dir_name = fs.path.dirname(path)
        the_file_name = fs.path.basename(path)
        the_fs = fs.open_fs(dir_name)
        f = the_fs.openbin(the_file_name)
    try:
        yield f
    finally:
        f.close()
        the_fs.close()


@log_fs_failure
def read_unicode(path):
    with open_file(path) as file_handle:
        return file_handle.read()


@log_fs_failure
def read_bytes(path):
    with open_binary_file(path) as file_handle:
        return file_handle.read()


read_binary = read_bytes


@log_fs_failure
def write_bytes(filename, bytes_content):
    filename = to_unicode(filename)
    if "://" in filename:
        zip_file, folder = url_split(filename)
        with fs.open_fs(zip_file, create=True) as the_fs:
            the_fs.writebytes(folder, bytes_content)
    else:
        dir_name = fs.path.dirname(filename)
        the_file_name = fs.path.basename(filename)
        with fs.open_fs(dir_name) as the_fs:
            the_fs.writebytes(the_file_name, bytes_content)


@log_fs_failure
def is_dir(path):
    folder_or_file, path = _path_split(path)
    with fs.open_fs(folder_or_file) as the_fs:
        return the_fs.isdir(path)


@log_fs_failure
def is_file(path):
    folder_or_file, path = _path_split(path)
    with fs.open_fs(folder_or_file) as the_fs:
        return the_fs.isfile(path)


@log_fs_failure
def exists(path):
    path = to_unicode(path)

    if is_zip_alike_url(path):
        zip_file, folder = url_split(path)
        try:
            with fs.open_fs(zip_file) as the_fs:
                if folder:
                    return the_fs.exists(folder)
                return True
        except fs.errors.CreateFailed:
            return False
    dir_name = fs.path.dirname(path)
    the_file_name = fs.path.basename(path)

    try:
        with fs.open_fs(dir_name) as the_fs:
            return the_fs.exists(the_file_name)
    except fs.errors.CreateFailed:
        return False


@log_fs_failure
def list_dir(path):
    path = to_unicode(path)
    folder_or_file, path = _path_split(path)
    with fs.open_fs(folder_or_file) as the_fs:
        for file_name in the_fs.listdir(path):
            yield file_name


@log_fs_failure
def abspath(path):
    path = to_unicode(path)
    folder_or_file, path = _path_split(path)
    with fs.open_fs(folder_or_file) as the_fs:
        return the_fs.getsyspath(path)


@log_fs_failure
def fs_url(path):
    path = to_unicode(path)
    folder_or_file, path = _path_split(path)
    with fs.open_fs(folder_or_file) as the_fs:
        return the_fs.geturl(path)


def to_unicode(path):
    if PY2 and path.__class__.__name__ != "unicode":
        return u"".__class__(path)
    return path


def is_zip_alike_url(url):
    specs = ["zip://", "tar://"]
    for prefix in specs:
        if url.startswith(prefix):
            return True
    else:
        return False


def url_split(url):
    result = urlparse(url)

    if url.endswith(result.scheme):
        url_to_file = url
        path = None
    else:
        url_to_file, path = url.split(result.scheme + "/")
        url_to_file = url_to_file + result.scheme

    return url_to_file, path


def _path_split(url_or_path):
    url_or_path = to_unicode(url_or_path)
    if is_zip_alike_url(url_or_path):
        return url_split(url_or_path)
    else:
        return fs.path.dirname(url_or_path), fs.path.basename(url_or_path)
