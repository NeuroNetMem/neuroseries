import inspect
import os
import os.path
import os.path
import sys
from subprocess import Popen, PIPE

import git

ROOT_PREFIX = None

repos = []

dependencies = []


def get_caller(back=1):
    """
    get the main parameters of a calling function
    :param back: how many frames back in the stack you should go
    :return: a dict with fields 'filename', 'lineno', and 'function'
    """
    frame_caller = inspect.stack()[back]
    caller = {'filename': frame_caller[1], 'lineno': frame_caller[2],
              'function': frame_caller[3]}
    return caller


def get_entry_point():
    """
    get the entry point of a python script
    :return: a dict with fields: 'entry_script': the filename of the entry script,
    'entry_args': the arguments list with which it was called
    """
    frame_entry = inspect.stack()[-1]
    import sys
    entry = {'entry_script': frame_entry[1], 'entry_args': sys.argv}
    return entry


def get_repo_info(dir_name):
    """
    find the repository that contains the given directory
    :param dir_name: directory to be examined
    :return: a dict with fields 'working_tree_dir': hte
    """

    try:
        repo = git.Repo(dir_name, search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        raise ValueError("no repository at " + dir_name)
    is_dirty = repo.is_dirty(untracked_files=True)
    repo_info = {'working_tree_dir': repo.working_tree_dir, 'commit': repo.head.ref.commit.hexsha,
                 'remote': repo.remotes.origin.url}
    return repo_info, is_dirty, repo


def is_repo_notebook_clean():
    """
    Tells you whether the script repository is clean except for the current notebook
    Returns: True if the repo is clean

    """

    from dataman import track_info
    script_repo_info, is_dirty, script_repo = get_repo_info(os.path.dirname(track_info['entry_point']))
    if not is_dirty:
        return True

    d = script_repo.index.diff(None)
    if len(d) > 1:
        return False

    changed_file = d[0].a_path

    _, notebook_path = get_notebook_name()
    from dataman.data_manager import track_info
    working_tree = track_info['repos'][0]['working_tree_dir']
    notebook_name = os.path.relpath(notebook_path, working_tree)

    if changed_file != notebook_name:
        return False

    return True


def commit_notebook():
    """
    commit the notebook (e.g. prior to saving data)
    Returns:
        True if the repo is now clean
        False otherwise

    """
    from dataman import track_info
    script_repo_info, is_dirty, script_repo = get_repo_info(os.path.dirname(track_info['entry_point']))
    ix = script_repo.index
    notebook_name, _ = get_notebook_name()
    ix.add(notebook_name)
    ix.commit("committing " + notebook_name)
    return not script_repo.is_dirty()


def in_ipynb():
    """
    determines if we are running within a ipython notebook
    :return: True if we are running in a notebook, False otherwise
    """
    try:
        # noinspection PyUnresolvedReferences,PyUnusedLocal
        cfg = get_ipython().config
        # if cfg['IPKernelApp']['parent_appname'] == 'ipython-notebook':
        #     return True
        # else:
        #     return False
        return True
    except NameError:
        return False


def run_magic(magic_string="timeit abs(-42)"):
    """
    runs a ipython magic command
    :param magic_string: the magic command
    :return: None
    """
    from IPython import get_ipython
    ipython = get_ipython()
    if ipython:
        ipython.magic(magic_string)


def fetch_notebook_name():
    """
    Fetches the notebook name via javascript so that it is available to get_notebook_name from the next cell
    :return: None
    """
    from IPython import get_ipython
    ipython = get_ipython()
    if ipython:
        ipython.run_cell_magic('javascript', '',
                               """
var kernel = Jupyter.notebook.kernel;
var command = ["notebookPath = ",
    "'", window.document.body.dataset.notebookPath, "'" ].join('')
kernel.execute(command)
var command = ["notebookName = ",
    "'", window.document.body.dataset.notebookName, "'" ].join('')
kernel.execute(command)
""")


def get_notebook_name(prefix=None):
    """
    Obtains ipython notebook path and name.

    This is an ugly hack, with an unfriendly user interface, but it is
    apparently the best we can do since jupyter doesn't expose the notebook path other than via javascript from the
    browser, and that has its own limitations. In order for this to work properly, the user must:
    1. Start the notebook server (under unix as jupyter notebook) from your home directory. If you choose not to do so
    then you have to specify the directory from which the server was started as the prefix argument here.
    2. reload the notebook in the browser after renaming the notebook, otherwise you will get a non-updated name.
    3. in a *previous cell* call save_notebook or fetch_notebook_name. The notebook name won't be available to this
    function until the cell in which one of these two function has been called has completed execution.

    :param prefix: the directory from which the notebook server is started
    (by default, the root of the git repo)
    :return: notebook_name: the notebook file name notebook_path: the notebook path name
    """
    if not prefix:
        from dataman.data_manager import track_info
        prefix = track_info['repos'][0]['working_tree_dir']

    stack = inspect.stack()
    notebook_path = ''
    notebook_name = ''
    for back in range(1, len(stack)):
        frame_caller = stack[back]
        # print(frame_caller[0].f_locals.keys())
        try:
            notebook_name = frame_caller[0].f_locals['notebookName']
            notebook_path = frame_caller[0].f_locals['notebookPath']
            notebook_path = os.path.join(prefix, notebook_path)
            break
        except KeyError:
            pass

    if notebook_name == '':
        raise RuntimeError("""Could not retrieve notebook path.
    If you are running a notebook, you need to call fetch_notebook or save_notebook from a previous cell.""")

    return notebook_name, notebook_path


def save_notebook():
    """
    Forces saving of the ipython notebook, raises RunTimeError if not in notebook,
    Also fetches the notebook name
    :return: None
    """
    from IPython import get_ipython
    ipython = get_ipython()
    if ipython:
        ipython.run_cell_magic('javascript', '',
                               """IPython.notebook.save_notebook();""")
        fetch_notebook_name()
    else:
        raise RuntimeError("Apparently not running a notebook at the moment")


def call_conda(extra_args, abspath=True):
    """
    calls conda in the virtual env where we are running from
    :param extra_args: the arguments to the conda call
    :param abspath: if True runs from the absolute path
    :return: stdout, stderr streams with conda output
    """
    # call conda with the list of extra arguments, and return the tuple
    # stdout, stderr (adapted from conda-api code)

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

    env1 = os.environ.copy()
    if 'PYTHONEXECUTABLE' in env1:
        del env1['PYTHONEXECUTABLE']

    try:
        if abspath:
            p = Popen(' '.join(cmd_list), stdout=PIPE, stderr=PIPE, shell=True, env=env1)
        else:
            # unix_path = os.getenv('PATH')
            # p = Popen(cmd_list, stdout=PIPE, stderr=PIPE, env={'PYTHONPATH': '', 'PATH': unix_path})
            p = Popen(cmd_list, stdout=PIPE, stderr=PIPE, shell=True, env=env1)
    except OSError:
        raise Exception("could not invoke {}\n".format(extra_args))
    return p.communicate()


def get_environment_yml():
    """
    gets the current environment in a form that can be used by conda to replicate it
    :return: a string including the content of the environment.yml file
    """

    s_out, s_err = call_conda(('env', 'export'))
    import re
    if len(s_err) > 0 and not re.match(r"^DEPRECATION", s_err.decode()):
        raise RuntimeError("conda failed with error: " + s_err.decode())
    return s_out.decode()

if __name__ == '__main__':

    stdout, stderr = call_conda(('env', 'export'))
    print(stdout.decode('utf-8'))
    print(stderr)
