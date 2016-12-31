import json

import numpy as np
import pandas as pd
import os

from dataman.tracker_utils import get_repo_info, in_ipynb, get_environment_yml
from .git_annex import AnnexRepo

_dont_check_git = False
_no_git_repo = False


def check_git_repos(when_dirty='warn'):
    import warnings
    _, is_dirty, script_repo = get_repo_info(os.path.dirname(track_info['entry_point']))

    if not _dont_check_git and is_dirty and not in_ipynb():
        if when_dirty == 'warn':
            warnings.warn("""Running from a dirty git repository (and not from a notebook).\n
         Please commit your changes before running. You will not be able to save data
                                 from this run""")
        else:
            raise RuntimeError("""Running from a dirty git repository (and not from a notebook).\n
                                  Please commit your changes before running""")

    if not _dont_check_git and is_dirty:
        d = script_repo.index.diff(None)
        if len(d) > 1:
            if when_dirty == 'warn':
                warnings.warn("""Running from a dirty git repo (besides the current notebook).
                                 Please commit your changes before running. \nYou will not be able to save data
                                 from this run""")
            else:
                raise RuntimeError("""Running from a dirty git repo (besides the current notebook).\n
                                      Please commit your changes before running""")

    print("len repos:")
    print(len(track_info['repos']))
    for repo in track_info['repos']:
        print(repo)
        _, is_dirty, _ = get_repo_info(repo['working_tree_dir'])
        if is_dirty:
            if when_dirty == 'warn':
                warnings.warn("Dependency repository " + repo['working_tree_dir'] + " is dirty, please commit!\n" +
                              "You will not  be able to save data from this run ")
            else:
                raise RuntimeError("Dependency repository " + repo['working_tree_dir'] + " is dirty, please commit!")


# noinspection PyProtectedMember
def _get_init_info():
    """This gets all the needed information about the run at the beginning.

    It is automatically called at module import
    Returns:
        a dict about the information
    """
    # this gets all the needed information at the beginning of the run
    info = {}

    # define a random UUID
    from uuid import uuid4
    info['uuid'] = str(uuid4())

    # report the time of run start
    from time import time
    info['run_time'] = str(time())

    # get name of the entry point and the arguments
    from sys import argv
    import os.path
    if in_ipynb():
        info['entry_point'] = '###notebook'
        info['args'] = []
    else:
        info['entry_point'] = os.path.realpath(argv[0])
        info['args'] = argv[1:]

    # get git status, if it's a script, this should be completely committed,
    # if it's a notebook everything should be committed
    # except for the notebook itself (which may be committed at the save time)
    repos = []

    if _no_git_repo:
        script_repo_info = {'working_tree_dir': ''}
    else:
        script_repo_info, is_dirty, script_repo = get_repo_info(os.path.dirname(info['entry_point']))

    repos.append(script_repo_info)

    # open config file, get git repos to be tracked, eventual files that need to be included in the dependencies
    # (e.g. lookup tables, etc.)
    # config file can be 1) in the current directory, named neuroseries.yml,
    # 2) in the 'project' directory (root of the containing git repo
    # 3) in the home directory as .neuroseries/config.yaml
    # 4) at the location pointed to by the variable NEUROSERIES_CONFIG

    config_candidates = ['./neuroseries.yml']

    import os.path
    config_candidates.append(os.path.join(repos[0]['working_tree_dir'], 'neuroseries.yml'))

    config_candidates.append('~/.neuroseries/config.yml')

    import os
    if 'NEUROSERIES_CONFIG' in os.environ:
        config_candidates.append(os.environ['NEUROSERIES_CONFIG'])

    import yaml
    config = {}
    for config_file in config_candidates:
        try:
            with open(os.path.expanduser(config_file)) as source:
                config = yaml.load(source)
                print('found config file at ' + config_file)
                break
        except FileNotFoundError:
            pass

    extra_repos = []
    info['config'] = config
    if 'extra_repos' in config:
        extra_repos.extend(config['extra_repos'])

    for r in extra_repos:
        script_repo_info, is_dirty, script_repo = get_repo_info(r)
        repos.append(script_repo_info)

    info['repos'] = repos

    # get venv status
    venv = get_environment_yml()
    info['venv'] = venv

    # get os information
    import platform
    os_info = dict(platform.uname()._asdict())
    info['os'] = os_info

    # get hardware information

    import psutil
    # noinspection PyProtectedMember
    mem_info = dict(psutil.virtual_memory()._asdict())
    info['memory'] = mem_info

    return info

track_info = _get_init_info()
check_git_repos('warn')

dependencies = []


def get_dependencies():
    return dependencies


def reset_dependencies():
    global dependencies
    dependencies = []


def str_to_series(a_string):
    """Helper function to convert strings
    This is mostly intended for json converted information, which is turned into a pandas series for storage in a
     pd.HDFStore. Only ASCII strings are supported

    Args:
        a_string: string to be converted

    Returns:
        a pd.Series
    """
    ba = bytearray(a_string, encoding='utf-8')
    ss = pd.Series(ba)
    return ss


def series_to_str(ss):
    """Helper function to convert a string encoded into a series

    Args:
        ss: a pd.Series encoded with str_to_series

    Returns: the decoded string

    """
    bb = bytearray(ss.values.tolist())
    bs = bytes(bb)
    a_string = bs.decode()
    return a_string


# noinspection PyClassHasNoInit
class PandasHDFStoreWithTracking(pd.HDFStore):
    """Enhanced pd.HDFStore including tracking information and metadata"""
    def get_info(self):
        """get information from file

        Returns: the information as a string

        """
        ss = self['file_info']
        return series_to_str(ss)

    def put_info(self, info):
        """
        Store info in the file
        Args:
            info: an information string

        Returns:
            None

        """
        ss = str_to_series(info)
        self.put('file_info', ss)

    def get_with_metadata(self, key):
        """get data with metadata

        Args:
            key: the variable name

        Returns:
            data: a pd.Series object (or nd.array)
            metadata: a dict with the metadata
        """
        data = self[key]
        metadata = None
        attr = self.get_storer(key).attrs
        if hasattr(attr, 'metadata'):
            metadata = attr.metadata

        return data, metadata

    def get(self, key):
        """Retrieves data from a store
        Pandas object and ndarray (via a pandas wrapper) are supported
        Args:
            key: the variable name

        Returns:
            data: the data

        """
        import ast
        data = super().get(key)
        attr = self.get_storer(key).attrs
        if attr is not None and hasattr(attr, 'metadata') and attr.metadata is not None and \
                        'class' in attr.metadata and attr.metadata['class'] == 'ndarray':
            data = data.values
            data_shape = ast.literal_eval(attr.metadata['shape'])
            data = data.reshape(data_shape)
        return data

    def put_with_metadata(self, key, value, metadata, **kwargs):
        """put data that needs ot be recorded with metadata

        Args:
            key: the variable name
            value: a pandas or ndarray
            metadata: a dict with the metadata
            **kwargs: additional arguments to be passed to store

        Returns:
            None

        """
        self.put(key, value, **kwargs)
        attr = self.get_storer(key).attrs

        if metadata is None:
            metadata = {}
        if hasattr(attr, 'metadata'):
            ex_metadata = attr.metadata
            metadata.update(ex_metadata)

        self.get_storer(key).attrs.metadata = metadata

    def put(self, key, value, **kwargs):
        """Put data in the store
        Handles pandas and ndarray types (the latter via a pandas wrapper)
        Args:
            key: the variable name
            value: a pandas or ndarray object
            **kwargs: optional arguments to be passed to pd.HDFStore

        Returns:
            None
        """
        if isinstance(value, np.ndarray):
            shape_str = str(value.shape)
            if value.ndim <= 2:
                value = pd.DataFrame(value)
            else:
                value = pd.Panel(value)
            super().put(key, value, **kwargs)
            metadata = {'class': 'ndarray', 'shape': shape_str}
            self.get_storer(key).attrs.metadata = metadata
        else:
            super().put(key, value, **kwargs)


class _GenericStore(object):
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def get_info(self):
        pass

    def put_info(self, info):
        pass

    def close(self):
        pass


class FilesBackend(object):
    def fetch_file(self, filename):
        pass

    def repo_info(self, filename):
        return {'backend': 'FilesBackend', 'file': filename}

    def save_metadata(self, filename, info):
        pass

    def commit(self, filename, message_add=None):
        pass

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_file_info(self, filename):
        return None


default_backend = FilesBackend()


def set_default_backend(backend):
    global default_backend
    default_backend = backend


def get_hash_sha256(filename):
    import hashlib
    h256 = hashlib.sha256()

    f = open(filename, 'rb')

    for chunk in iter(lambda: f.read(4096), b""):
        h256.update(chunk)

    my_hash = h256.hexdigest()
    return my_hash


class JsonBackend(FilesBackend):
    def repo_info(self, filename):
        return {'backend': 'JsonBackend', 'file': filename}

    def save_metadata(self, filename, info):
        hash_file = get_hash_sha256(filename)
        info['hash'] = hash_file
        import os.path
        root, _ = os.path.splitext(filename)
        json_file = root + '.json'
        with open(json_file, 'w') as f:
            f.write(json.dumps(info))

    def get_file_info(self, filename):
        import os
        root, _ = os.path.splitext(filename)
        json_file = root + '.json'
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                js_string = f.read()
            return json.loads(js_string)
        else:
            file_hash = self.get_hash('filename')
            info = {'file': filename, 'hash': file_hash}
            info.update(self.repo_info(filename))
            return info

    def get_hash(self, filename):
        return get_hash_sha256(filename)


class AnnexJsonBackend(JsonBackend):
    def __init__(self, dir_name=None, clone_from=None, new_repo=False, description=''):
        """Starts a new backend with git-annex support.
        Metadata are written in json files with the same name and '.json'
        extension. If new_repo is False, a git annex repo is searched for in:
        1) in dir_name
        2) in an 'annex' field of the config file
        3) in the current directory
        4) in current directory's parents
        Args:
            dir_name: The starting point for repo search
            clone_from: a URL containing a clonable repo
            new_repo: if True, a new repo will be created at dir_name or current directory
            description: a description to identify the current repo
        """
        import os
        import git
        if dir_name is None:
            if 'annex' in track_info['config']:
                dir_name = track_info['annex']
            else:
                dir_name = os.getcwd()
        dir_name = os.path.expanduser(dir_name)
        if not new_repo:  # then search for a git repo in parent dirs
            repo = git.Repo(dir_name, search_parent_directories=True)
            dir_name = repo.working_tree_dir
        self.repo = AnnexRepo(dir_name, clone_from=clone_from, description=description)

    def fetch_file(self, filename):
        """Attempts to ensure availability of file
        File will be looked for in remotes if not locally available
        Args:
            filename: the filename to be searched

        Returns: None

        """
        self.repo.get(filename)

    def repo_info(self, filename):

        """Get Backend-specific information

        Returns: a dict with the info

        """
        repo_info = {'backend': 'AnnexJsonBackend'}
        repo_info.update(self.repo.repo_info(filename))
        return repo_info

    def save_metadata(self, filename, info):
        """Saves file metadata in JSON file

        Args:
            filename: the filename the metadata is added for
            info: tracking information. The file hash is added here

        Returns:
            None

        """
        self.repo.add_annex(filename)
        hash_file = self.repo.lookupkey(filename)
        info['hash'] = hash_file
        import os.path
        root, _ = os.path.splitext(filename)
        json_file = root + '.json'
        with open(json_file, 'w') as f:
            f.write(json.dumps(info))
        self.repo.add(json_file)

    def commit(self, filename, message_add=None):
        """Commit the changes to git

        Args:
            filename: the file name to commit
            message_add: an additional message after the standard
            "Ran script.py. Added data.h5"

        Returns:
            None

        """
        import sys
        message = 'Ran ' + sys.argv[0] + '. Added ' + filename + '. '
        if message_add:
            message += message_add
        self.repo.commit(message)

    def get_hash(self, filename):
        return self.repo.lookupkey(filename)

    def push(self, remote_name):
        self.repo.push(remote_name)


def capture_info(item):
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        item.info()
    out = f.getvalue()
    return out


class TrackingStore(object):
    """A Store, encapsulating a file, that will keep track of code that has been run and its dependencies.
    What it does
    at construction
    1) fetch data wherever they are (backend)
    2) generate material store, material store should be able to handle pandas object (e.g. HDFStore)
    3) if read: get the tracking info if present add it to dependencies,
    if not generate file fingerprint, store that as tracking info
    4) if write: dump information
    file information is a dict {'file': filename, 'hash': an hash for the file, for example the SHA256 from git-annex,
    'date-created': a date string, 'run': track_info, 'dependencies': all the dependencies,
    'repo_info': information useful for the backend to retrieve the file
    'variables': a dict of variable names and info (as for example given by
    information is serialized as json and stored in the material store (backend)
    information also stored in json (text) metafile. before the file is closed,
    the hash will be the placeholder 'NULL'.
    it will be replaced in the metafile by the hash at closure

    material store must
    handle pandas objects, with metadata. Must be able to store (ASCII) info string
    must be able to write and read with or without metadata (for pandas)
    it can only do write and read, no append (enforced in this class)

    backend must
    fetch file (ensure availability)
    provide hash
    handle metafile info (or other mechanism). metafile info
    commit file and metafile (for example, at closure)
    for git-annex that would mean: data files in the annex, metafiles in the git repo #TODO

    backend is defined once per run and remains a property of run TODO
    """

    def __init__(self, filename, mode='r', backend=None, store_type=PandasHDFStoreWithTracking, comment=None,
                 **kwargs):
        """Initialize the Store

        Args:
            filename: The filename
            mode: can be 'r' (read) or 'w' (write)
            backend: the backend for file handling
            store_type: the class to be used for material store
            **kwargs: optional arguments, will be passed to the material store
        """
        check_git_repos(when_dirty='error')
        global dependencies
        if mode not in ['r', 'w']:
            raise ValueError('mode must be "w" or "r"')
        self.mode = mode
        self.filename = filename
        if backend:
            self.backend = backend
        else:
            self.backend = default_backend
        if mode == 'r':
            self.backend.fetch_file(filename)

        self.store = store_type(filename, mode, **kwargs)

        if mode == 'r':
            self.info = self.backend.get_file_info(self.filename)
            if self.info is None:  # if backend can't help, let's look into the store
                self.info = json.loads(self.store.get_info())

            if self.info is not None:
                dependencies.append(self.info)
        else:
            import datetime
            repo_info = self.backend.repo_info(self.filename)
            self.info = {'run': track_info, 'date_created': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         'dependencies': dependencies, 'file': filename, 'hash': 'NULL', 'repo_info': repo_info,
                         'variables': {}}
            if comment:
                self.info['comment'] = comment

            self.store.put_info(json.dumps(self.info))
        print(dependencies)

    def close(self):
        """Close the store
        Does housekeeping with the tracking information and backend
        Returns:
            None
        """
        if self.mode == 'w':
            self.info['run'] = track_info
            self.store.put_info(json.dumps(self.info))
        self.store.close()
        self.backend.save_metadata(self.filename, self.info)
        self.backend.commit(self.filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get(self, key):
        """Gets data from store

        Args:
            key: the variable name

        Returns:
            the data
        """
        if self.mode == 'w':
            raise IOError("store is open in write mode")
        return self.store.get(key)

    def has_metadata(self, key):
        """checks if stored data has accompanying metadata

        Args:
            key: the variable name

        Returns:
            bool
        """
        if self.mode == 'w':
            raise IOError("store is open in write mode")
        (_, metadata) = self.store.get_with_metadata(key)
        return metadata is not None

    def get_with_metadata(self, key):
        """Get data with metadata

        Args:
            key: the variable name

        Returns:
            data: the data
            metadata: dict with metadata

        """
        if self.mode == 'w':
            raise IOError("store is open in write mode")
        return self.store.get_with_metadata(key)

    def keys(self):
        """lists the variables stored

        Returns:
            list of variable names

        """
        return self.store.keys()

    def put(self, key, value, metadata=None, **kwargs):
        """Put data in store

        Args:
            key: the variable name
            value: data
            metadata: dict with metadata
            **kwargs: optional arguments to be passed to material store

        Returns:
            None

        """
        if self.mode == 'r':
            raise IOError('store is open in read mode')
        self.info['variables'][key] = self.get_variable_info(key, value)

        self.store.put_with_metadata(key, value, metadata, **kwargs)

    def __setitem__(self, key, value):
        self.put(key, value)

    def __getitem__(self, item):
        return self.get(item)

    def get_file_info(self):
        """Returns the tracking information about the file

        Returns:
            a dict with all the stored information

        """
        backend_info = self.backend.get_file_info(self.filename)
        if backend_info:
            return backend_info
        return json.loads(self.store.get_info())

    def append(self, key, value, **kwargs):
        """Appends data to existing variable (if store allows it)

        Args:
            key: the variable name
            value: data to append
            **kwargs: optional arguments for the material store

        Returns:
            None

        """
        if self.mode == 'r':
            raise IOError('store is open in read mode')
        self.info['variables'][key] = self.get_variable_info(key, value)
        self.store.append(key, value, **kwargs)

    def get_variable_info(self, key, var):
        """Get information about a variable stored in the store

        Args:
            key: the key to the variable in the store
            var: the variable value

        Returns:
            A string including a description of the variable as obtained from Pandas or at the very least the type and
            shape of the variable

        """
        info = "Object of class: " + type(var).__name__ + '\n'
        try:
            i = capture_info(self.store[key])
            if i:
                info += i
        except (AttributeError, KeyError):
            try:
                i = capture_info(var)
                if i:
                    info += i
            except AttributeError:
                try:
                    s = str(var.shape)
                    info += 'Shape: ' + s
                except AttributeError:
                    import warnings
                    warnings.warn("Cannot determine info for variable. ")
        return info


HDFStore = TrackingStore


def store_file(filename, backend=None, comment=None):
    # noinspection PyTypeChecker
    store = TrackingStore(filename, mode='w', store_type=_GenericStore,  backend=backend, comment=comment)
    store.close()


def register_input(filename, backend=None):
    # noinspection PyTypeChecker
    store = TrackingStore(filename, mode='r', store_type=_GenericStore, backend=backend)
    store.close()
