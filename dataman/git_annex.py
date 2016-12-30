import git


class MyProgressPrinter(git.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")


class AnnexRepo(object):
    def __init__(self, path=None, clone_from=None, description=''):
        if path is None:
            import os
            path = os.getcwd()
        self.working_tree = path
        if clone_from:
            self.repo = git.Repo.clone_from(clone_from, to_path=path, progress=MyProgressPrinter)
            self.git = self.repo.git
            cmd_list = ['git', 'annex', 'init']
            if description:
                cmd_list.append('"' + description + '"')
            self.git.execute(cmd_list)
        else:
            self.repo = git.Repo.init(path)
            self.git = self.repo.git
            cmd_list = ['git', 'annex', 'init']
            if description:
                cmd_list.append('"' + description + '"')
            self.git.execute(cmd_list)
        self.remotes = {}
        self.is_special = {}
        import collections
        self.special_urls = collections.defaultdict(lambda: 'None')
        self.special_type = {}

    def path_in_repo(self, filename):
        import os
        path = os.path.relpath(os.path.abspath(filename), self.repo.working_tree_dir)
        return path

    def add_annex(self, file):
        file = self.path_in_repo(file)
        cmd_list = ['git', 'annex', 'add', file]
        self.git.execute(cmd_list)

    def add(self, file):
        file = self.path_in_repo(file)
        self.repo.index.add([file])

    def commit(self, message):
        self.repo.index.commit(message)

    def add_remote(self, name, remote_url):
        self.remotes[name] = self.repo.create_remote(name, remote_url)
        self.is_special[name] = False
        origin = self.remotes[name]
        origin.fetch()
        self.repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
    # def add_special_remote(self, name, remote_url, remote_type='rsync', auto_enable=True, **kwargs):
    #     special_types = {'rsync': self.add_special_remote_rsync}
    #     try:
    #         special_types[remote_type](name, remote_url, auto_enable, **kwargs)
    #     except KeyError:
    #         raise NotImplementedError("remote type not implemented. Types implemented are: "
    #                                   + str(special_types.keys()))

    # noinspection PyUnusedLocal

    def pull(self, remote_name):
        self.remotes[remote_name].pull()

    def push(self, remote_name):
        self.remotes[remote_name].push()

    # noinspection PyUnusedLocal
    def add_special_remote_rsync(self, name, remote_url, auto_enable=True, **kwargs):
        cmd_list = ['git', 'annex', 'initremote', name, 'type=rsync', 'rsyncurl=' + remote_url, 'encryption=none']
        if auto_enable:
            cmd_list.append('autoenable=true')
        self.git.execute(cmd_list)
        self.remotes[name] = self.repo.remotes[name]
        self.is_special[name] = True
        self.special_urls[name] = remote_url
        self.special_type[name] = 'rsync'

    def get(self, file):
        file = self.path_in_repo(file)
        cmd_list = ['git', 'annex', 'get', file]
        self.git.execute(cmd_list)

    def drop(self, file):
        file = self.path_in_repo(file)
        cmd_list = ['git', 'annex', 'drop', file]
        self.git.execute(cmd_list)

    def push_annex(self, remote_name):
        cmd_list = ['git', 'annex', 'sync', '--content', '--no-pull', self.remotes[remote_name].name]
        self.git.execute(cmd_list)

    def lookupkey(self, filename):
        filename = self.path_in_repo(filename)
        cmd_list = ['git', 'annex', 'lookupkey', filename]
        key = self.git.execute(cmd_list)
        return key

    def repo_info(self, file):
        normal_remotes = [k for k in self.remotes.keys() if not self.is_special[k]]
        normal_remotes_info = {k: {'name': self.remotes[k].name, 'url': self.remotes[k].url} for k in normal_remotes}

        special_remotes = [k for k in self.remotes.keys() if self.is_special[k]]
        special_remotes_info = {k: {'name': self.remotes[k].name, 'url': self.special_urls[k],
                                    'type': self.special_type} for k in special_remotes}

        path = self.path_in_repo(file)
        info = {'working_tree_dir': self.repo.working_tree_dir, 'remotes': normal_remotes_info,
                'special_remotes': special_remotes_info, 'path': path}
        return info
