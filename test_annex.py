import unittest
# from nose_parameterized import parameterized
import pexpect as pex

# noinspection PyUnresolvedReferences
import neuroseries as nts

import random
import string

rsync_host = 'tompouce.science.ru.nl'
rsync_user = 'fpbatta'
rsync_root = '/var/services/homes/fpbatta/test_annex'


def make_random_text(length):
    text = "".join([random.choice(string.ascii_letters) for _ in range(length)])
    return text


def get_sha256(filename):
    import hashlib
    h256 = hashlib.sha256()
    f = open(filename, 'rb')

    for chunk in iter(lambda: f.read(4096), b""):
        h256.update(chunk)

    my_hash = h256.hexdigest()
    return my_hash


def change_mod(the_dir):
    import os
    for root, dirs, files in os.walk(the_dir):
        for d in dirs:
            try:
                os.chmod(os.path.join(root, d), 0O755)
            except FileNotFoundError:
                pass
        for f in files:
            try:
                os.chmod(os.path.join(root, f), 0O644)
            except FileNotFoundError:
                pass


def prepare_sandbox():
    import os
    import shutil
    try:
        change_mod('scratch/sandbox')
    except BaseException as a:
        print('change mod')
        print(type(a))
        print(a)

    try:
        shutil.rmtree('scratch/sandbox', ignore_errors=True)
    except BaseException as a:
        print('rmtree')
        print(type(a))
        print(a)

    os.makedirs('scratch/sandbox')


class InitAnnexTestCase(unittest.TestCase):
    def setUp(self):
        # noinspection PyGlobalUndefined
        global nts
        # noinspection PyUnresolvedReferences
        import neuroseries as nts
        import os
        # noinspection PyBroadException

        self.start_dir = os.getcwd()

        # noinspection PyBroadException

        prepare_sandbox()

        os.chdir('scratch/sandbox')

    def tearDown(self):
        import sys
        del sys.modules[nts.__name__]
        del sys.modules[nts.data_manager.__name__]

        import os
        import shutil
        print(self.start_dir)
        os.chdir(self.start_dir)
        # noinspection PyBroadException
        try:
            change_mod('scratch/sandbox')
            shutil.rmtree('scratch/sandbox')
        except:
            pass

    def test_init_repo_new(self):
        import os
        os.mkdir('repo1')
        os.chdir('repo1')

        self.annex = nts.AnnexRepo()
        ch = pex.spawn('git status')
        self.assertEqual(ch.expect('On branch master.*'), 0)

    def test_init_repo_existing(self):
        import os
        os.mkdir('repo1')
        os.chdir('repo1')
        pex.run('git init')
        pex.run('git annex init')

        self.annex = nts.AnnexRepo()
        ch = pex.spawn('git status')
        self.assertEqual(ch.expect('On branch master.*'), 0)

    def test_init_repo_clone(self):
        import os
        os.mkdir('repo2')
        os.chdir('repo2')
        pex.run('git init')
        pex.run('git annex init')
        f = open('file1.txt', 'w')
        f.write(make_random_text(1000))
        f.close()
        pex.run('git annex add file1.txt')
        pex.run('git commit -m "commit file1.txt"')
        os.chdir('..')
        os.mkdir('repo1')
        os.chdir('repo1')
        self.annex = nts.AnnexRepo(path=None, clone_from='../repo2')

        self.annex = nts.AnnexRepo()
        ch = pex.spawn('git status')
        self.assertEqual(ch.expect('On branch master.*'), 0)


class AnnexFilesTestCase(unittest.TestCase):
    def setUp(self):
        # noinspection PyGlobalUndefined
        global nts
        # noinspection PyUnresolvedReferences
        import neuroseries as nts
        import os
        # noinspection PyBroadException

        self.start_dir = os.getcwd()
        prepare_sandbox()
        os.chdir('scratch/sandbox')

        os.mkdir('repo1')
        os.chdir('repo1')
        pex.run('git init')
        pex.run('git annex init')

    def tearDown(self):
        import sys
        del sys.modules[nts.__name__]
        del sys.modules[nts.data_manager.__name__]

        import os
        import shutil
        print(self.start_dir)
        os.chdir(self.start_dir)
        # noinspection PyBroadException
        try:
            change_mod('scratch/sandbox')
            shutil.rmtree('scratch/sandbox')
        except:
            pass

    def test_add_file(self):
        f = open('file1.txt', 'w')
        f.write(make_random_text(1000))
        f.close()

        ch = pex.spawn('git status')
        self.assertEqual(ch.expect('.*Untracked files:.*file1.txt.*'), 0)

        self.annex = nts.AnnexRepo()
        self.annex.add('file1.txt')

        ch = pex.spawn('git status')
        self.assertEqual(ch.expect('.*new file.*file1.txt.*'), 0)

    def test_add_annex_file(self):
        import os
        f = open('file2.txt', 'w')
        f.write(make_random_text(1000))
        f.close()
        self.annex = nts.AnnexRepo()
        self.annex.add_annex('file2.txt')

        ch = pex.spawn('git status')
        self.assertEqual(ch.expect('.*new file.*file2.txt.*'), 0)

        self.assertTrue(os.path.islink('file2.txt'))


class AnnexRemoteTestCase(unittest.TestCase):
    def setUp(self):
        # noinspection PyGlobalUndefined
        global nts
        # noinspection PyUnresolvedReferences
        import neuroseries as nts
        import os
        # noinspection PyBroadException

        self.start_dir = os.getcwd()
        prepare_sandbox()
        os.chdir('scratch/sandbox')

        os.mkdir('repo1')
        os.chdir('repo1')
        pex.run('git init')
        pex.run('git annex init')

    def tearDown(self):
        import sys
        del sys.modules[nts.__name__]
        del sys.modules[nts.data_manager.__name__]

        import os
        import shutil
        print(self.start_dir)
        os.chdir(self.start_dir)
        # noinspection PyBroadException
        try:
            change_mod('scratch/sandbox')
            shutil.rmtree('scratch/sandbox')
        except:
            pass

    def create_remote_repo(self, name):
        import os
        os.mkdir(name)
        os.chdir(name)
        pex.run('git init')
        pex.run('git annex init')
        f = open('file1.txt', 'w')
        self.file1_content = make_random_text(1000)
        f.write(self.file1_content)
        f.close()
        pex.run('git annex add file1.txt')
        pex.run('git commit -m "commit file1.txt"')
        pex.run('git remote add laptop ../repo1')

    def test_add_remote(self):
        import os
        os.chdir('..')
        self.create_remote_repo('repo2')
        os.chdir('../repo1')
        self.repo = nts.AnnexRepo()
        # add a regular remote
        self.repo.add_remote('origin', '../repo2')
        # check that the remote is there
        self.assertEqual(self.repo.remotes['origin'].name, 'origin')
        info = self.repo.repo_info('file')
        url = info['remotes']['origin']['url']
        self.assertTrue(url, '../repo2')


    def test_pull(self):
        # test that data can be pulled to normal remote
        import os
        os.chdir('..')
        self.create_remote_repo('repo2')
        os.chdir('../repo1')
        self.repo = nts.AnnexRepo()
        self.repo.add_remote('origin', '../repo2')
        self.repo.pull('origin')
        self.assertTrue(os.path.islink('file1.txt'))
        target_path = os.readlink('file1.txt')
        self.assertFalse(os.path.exists(target_path))

        self.repo.get('file1.txt')
        self.assertTrue(os.path.islink('file1.txt'))
        with open('file1.txt', 'r') as f:
            retrieved_file1_content = f.read()
        self.assertEqual(retrieved_file1_content, self.file1_content)

        # now check that the getting an existing file doesn't cause issues
        self.repo.get('file1.txt')
        target_path = os.readlink('file1.txt')
        self.assertTrue(os.path.exists(target_path))

    def test_push_annex(self):
        import os
        os.chdir('..')
        self.create_remote_repo('repo2')
        os.chdir('../repo1')
        self.repo = nts.AnnexRepo()
        self.repo.add_remote('origin', '../repo2')
        self.repo.pull('origin')

        with open('file2.txt', 'w') as f:
            self.file2_content = make_random_text(1000)
            f.write(self.file2_content)

        self.repo.add_annex('file2.txt')
        self.repo.commit('adding file2')
        self.repo.push_annex('origin')

        # check that the file is OK to the other side

        os.chdir('../repo2')
        pex.run('git pull laptop master')
        with open('file2.txt', 'r') as f:
            retrieved_file2_content = f.read()
        self.assertEqual(retrieved_file2_content, self.file2_content)

        # now let's go back and drop the file
        os.chdir('../repo1')
        self.repo.drop('file2.txt')
        target_path = os.readlink('file2.txt')
        self.assertFalse(os.path.exists(target_path))

        self.repo.get('file2.txt')
        with open('file2.txt', 'r') as f:
            retrieved_file2_content = f.read()
        self.assertEqual(retrieved_file2_content, self.file2_content)

    def test_push(self):
        import os
        os.chdir('..')
        self.create_remote_repo('repo2')
        os.chdir('../repo1')
        self.repo = nts.AnnexRepo()
        self.repo.add_remote('origin', '../repo2')
        self.repo.pull('origin')

        with open('file2.txt', 'w') as f:
            self.file2_content = make_random_text(1000)
            f.write(self.file2_content)

        self.repo.add_annex('file2.txt')
        self.repo.commit('adding file2')
        self.repo.push('origin')

        # check that the file is OK to the other side

        os.chdir('../repo2')
        pex.run('git pull laptop master')
        self.assertTrue(os.path.islink('file2.txt'))
        target_path = os.readlink('file2.txt')
        self.assertFalse(os.path.exists(target_path))

    def test_lookupkey(self):
        import os
        os.chdir('..')
        self.create_remote_repo('repo2')
        os.chdir('../repo1')
        self.repo = nts.AnnexRepo()
        self.repo.add_remote('origin', '../repo2')
        self.repo.pull('origin')
        self.assertTrue(os.path.islink('file1.txt'))
        target_path = os.readlink('file1.txt')
        self.assertTrue(self.repo.lookupkey('file1.txt') in target_path)


class SpecialRemoteTestCase(unittest.TestCase):
    def setUp(self):
        # noinspection PyGlobalUndefined
        global nts
        # noinspection PyUnresolvedReferences
        import neuroseries as nts
        import os
        # noinspection PyBroadException

        self.start_dir = os.getcwd()
        prepare_sandbox()
        os.chdir('scratch/sandbox')

        os.mkdir('repo1')
        os.chdir('repo1')
        pex.run('git init')
        pex.run('git annex init')
        self.cleanup_remote()

    def tearDown(self):
        import sys
        del sys.modules[nts.__name__]
        del sys.modules[nts.data_manager.__name__]

        import os
        import shutil
        print(self.start_dir)
        os.chdir(self.start_dir)
        # noinspection PyBroadException
        try:
            change_mod('scratch/sandbox')
            shutil.rmtree('scratch/sandbox')
        except:
            pass
        self.cleanup_remote()

    @staticmethod
    def cleanup_remote():
        from pexpect import pxssh
        s = pxssh.pxssh()
        s.login(rsync_host, rsync_user)  # add password if no private key auth.
        s.sendline('rm -rf ~/test_annex/repo?')
        s.logout()

    def test_add_special_remote(self):
        import os
        self.repo = nts.AnnexRepo()
        rsync_url = rsync_host + ':' + os.path.join(rsync_root, 'repo1')
        self.repo.add_special_remote_rsync('rsyncer', rsync_url)
        self.assertIn('rsyncer', self.repo.remotes)
        info = self.repo.repo_info('file')
        url = info['special_remotes']['rsyncer']['url']
        self.assertTrue(url, rsync_url)

    def test_push_special(self):
        import os
        self.repo = nts.AnnexRepo()
        rsync_url = rsync_host + ':' + os.path.join(rsync_root, 'repo1')
        self.repo.add_special_remote_rsync('rsyncer', rsync_url)
        self.assertIn('rsyncer', self.repo.remotes)
        with open('file2.txt', 'w') as f:
            self.file2_content = make_random_text(1000)
            f.write(self.file2_content)

        self.repo.add_annex('file2.txt')
        self.repo.commit('adding file2')
        self.repo.push_annex('rsyncer')

        self.repo.drop('file2.txt')
        target_path = os.readlink('file2.txt')
        self.assertFalse(os.path.exists(target_path))

        self.repo.get('file2.txt')
        with open('file2.txt', 'r') as f:
            retrieved_file2_content = f.read()
        self.assertEqual(retrieved_file2_content, self.file2_content)
