from moban import repo
from moban.adapter.osfs import EnhancedOSFS
from moban.adapter.zipfs import EnhancedZipFS
from moban.plugins.library import LIBRARIES

import fs
import fs.path
from fs.osfs import OSFS
from fs.opener import Opener
from fs.opener.registry import registry

# FS_VERSION = _version_count(fs.__version__)


@registry.install
class PypiFSOpener(Opener):
    protocols = ["pypi"]

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        pypi_package_name, _, dir_path = parse_result.resource.partition("/")
        library_path = LIBRARIES.resource_path_of(pypi_package_name)
        root_path = fs.path.join(library_path, dir_path)
        osfs = OSFS(root_path=root_path)
        return osfs


@registry.install
class RepoFSOpener(Opener):
    protocols = ["repo"]

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        repo_name, _, dir_path = parse_result.resource.partition("/")
        actual_repo_path = fs.path.join(repo.get_moban_home(), repo_name)
        root_path = fs.path.join(actual_repo_path, dir_path)
        osfs = OSFS(root_path=root_path)
        return osfs


@registry.install
class ZipOpener(Opener):
    """`ZipFS` opener.
    """

    protocols = ["zip"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        if not create and writeable:
            raise fs.errors.NotWriteable(
                "Unable to open existing ZIP file for writing"
            )
        zip_fs = EnhancedZipFS(parse_result.resource, write=create)
        return zip_fs


@registry.install
class OSFSOpener(Opener):
    """`OSFS` opener.
    """

    protocols = ["file", "osfs"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> OSFS
        from os.path import abspath, expanduser, normpath, join

        _path = abspath(join(cwd, expanduser(parse_result.resource)))
        path = normpath(_path)
        osfs = EnhancedOSFS(path, create=create)
        return osfs


def _version_count(version):
    tokens = version.split(".")
    sum = 0
    for index, token in enumerate(reversed(tokens)):
        sum = sum + int(token) * (10 ** index)
    return sum
