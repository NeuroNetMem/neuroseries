import git


class MyProgressPrinter(git.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")


class AnnexRepo(object):
    def __init__(self, path, clone_from=None, description=''):
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

    def add_annex(self, file):
        cmd_list = ['git', 'annex', 'add', file]
        self.git.execute(cmd_list)

    def add(self, file):
        self.repo.index.add([file])

    def commit(self, message):
        self.repo.index.commit(message)

    def add_remote(self, name, remote_url):
        self.remotes[name] = self.repo.create_remote(name, remote_url)

    def add_special_remote(self, name, remote_url, remote_type='rsync', auto_enable=True, **kwargs):
        special_types = {'rsync': self.add_special_remote_rsync}
        try:
            special_types[remote_type](name, remote_url, auto_enable, **kwargs)
        except KeyError:
            raise NotImplementedError("remote type not implemented. Types implemented are: "
                                      + str(special_types.keys()))

    # noinspection PyUnusedLocal
    def add_special_remote_rsync(self, name, remote_url, auto_enable, **kwargs):
        cmd_list = ['git', 'annex', 'initremote', name, 'type=rsync', 'rsyncurl=' + remote_url, 'encryption=none']
        if auto_enable:
            cmd_list.append('autoenable=true')
        self.git.execute(cmd_list)

    def get(self, file):
        cmd_list = ['git', 'annex', 'get', file]
        self.git.execute(cmd_list)

    def push_remote(self, remote):
        cmd_list = ['git', 'annex' 'sync', '--content', '--no-pull', remote]
        self.git.execute(cmd_list)
