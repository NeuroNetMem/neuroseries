import inspect
import os.path
import git
import os
import sys
import json
from subprocess import Popen, PIPE
# from os.path import basename, isdir, join

ROOT_PREFIX = None

repos = []

dependencies = []


def get_caller_test():
    import sys

    print('argv')
    print(sys.argv)
    frame_caller = inspect.stack()[1]
    module = inspect.getmodule(frame_caller[0])
    print(frame_caller[0])
    print(module)
    print(dir(module))
    filename = module.__file__
    print(filename)
    print('from frame')
    print(frame_caller[1])
    print(os.path.dirname(filename))


def get_caller(back=1):
    frame_caller = inspect.stack()[back]
    caller = {'filename': frame_caller[1], 'lineno': frame_caller[2],
              'function': frame_caller[3]}
    return caller


def get_entry_point():
    frame_entry = inspect.stack()[-1]
    import sys
    entry = {'entry_script': frame_entry[1], 'entry_args': sys.argv}
    return entry


def get_repo(filename):
    repo = git.Repo(os.path.dirname(filename), search_parent_directories=True)
    is_dirty = repo.is_dirty()
    repo_info = {'working_tree_dir': repo.working_tree_dir, 'commit': repo.head.ref.commit.hexsha,
                 'remote': repo.remotes.origin.url}
    return repo_info, is_dirty, repo


def in_ipynb():
    try:
        pass
        # cfg = get_ipython().config
        # if cfg['IPKernelApp']['parent_appname'] == 'ipython-notebook':
        #     return True
        # else:
        #     return False
        return True
    except NameError:
        return False


def run_magic():
    from IPython import get_ipython
    ipython = get_ipython()
    if ipython:
        ipython.magic("timeit abs(-42)")


def call_conda(extra_args, abspath=True):
    # call conda with the list of extra arguments, and return the tuple
    # stdout, stderr

    if abspath:
        if sys.platform == 'win32':
            # python = join(ROOT_PREFIX, 'python.exe')
            # conda  = join(ROOT_PREFIX, 'Scripts', 'conda-script.py')
            # TODO must somehow specify the environment under win32
            raise NotImplementedError
        else:
            cmd_list = ['conda']
    else:  # just use whatever conda is on the path
        cmd_list = ['conda']

    cmd_list.extend(extra_args)

    try:
        if abspath:
            p = Popen(cmd_list, stdout=PIPE, stderr=PIPE)
        else:
            unix_path = os.getenv('PATH')
            p = Popen(cmd_list, stdout=PIPE, stderr=PIPE, env={'PYTHONPATH': '', 'PATH': unix_path})
    except OSError:
        raise Exception("could not invoke %r\n" % extra_args)
    return p.communicate()


def call_and_parse(extra_args, abspath=True):
    sout, serr = call_conda(extra_args, abspath=abspath)
    if stderr.decode().strip():
        raise Exception('conda %r:\nSTDERR:\n%s\nEND' % (extra_args,
                                                         stderr.decode()))
    return json.loads(stdout.decode())


if __name__ == '__main__':

    stdout, stderr = call_conda(('env', 'export'))
    print(stdout.decode('utf-8'))
    print(stderr)