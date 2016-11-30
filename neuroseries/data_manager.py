from .tracker_utils import get_repo_info, in_ipynb, get_environment_yml


# noinspection PyProtectedMember
def _get_init_info():
    # this gets all the needed information at the beginning of the run
    info = {}

    # get name of the entry point and the arguments
    import sys
    import os.path
    if in_ipynb():
        info['entry_point'] = '###notebook'
        info['args'] = []
    else:
        info['entry_point'] = os.path.realpath(sys.argv[0])
        info['args'] = sys.argv[1:]

    # get git status, if it's a script, this should be completely committed,
    # if it's a notebook everything should be committed
    # except for the notebook itself (which may be committed at the save time)
    repos = []

    script_repo_info, is_dirty, script_repo = get_repo_info(os.path.dirname(info['entry_point']))

    if is_dirty and not in_ipynb():
        raise RuntimeError("""Running from a dirty git repository (and not from a notebook).
        Please commit your changes before running""")

    if is_dirty:
        d = script_repo.index.diff(None)
        if len(d) > 1:
            raise RuntimeError("""Running from a dirty git repo (besides the current notebook).
            Please commit your changes before running""")

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

    config_candidates.append('.neuroseries/config.yml')

    import os
    if 'NEUROSERIES_CONFIG' in os.environ:
        config_candidates.append(os.environ['NEUROSERIES_CONFIG'])

    import yaml
    config = {}
    for config_file in config_candidates:
        try:
            with open(config_file) as source:
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
        if is_dirty:
            raise RuntimeError("Dependency repository " + r + "is dirty, please commit!")
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
    meminfo = dict(psutil.virtual_memory()._asdict())
    info['memory'] = meminfo

    return info

track_info = _get_init_info()
