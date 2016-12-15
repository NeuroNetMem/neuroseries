import unittest
# from nose_parameterized import parameterized
import pexpect as pex

import neuroseries as nts

import random
import string


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


class InitAnnexTestCase(unittest.TestCase):
    def setUp(self):
        # noinspection PyGlobalUndefined
        global nts
        import neuroseries as nts
        import os
        # noinspection PyBroadException

        self.start_dir = os.getcwd()

        # noinspection PyBroadException

        import shutil
        shutil.rmtree('scratch/sandbox')

        os.makedirs('scratch/sandbox')
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
            shutil.rmtree('scratch/sandbox')
        except:
            pass

    def test_init_repo_new(self):
        import os
        os.mkdir('repo1')
        os.chdir('repo1')

        self.annex = nts.AnnexRepo()
        ch = pex.spawn('git spawn')
        self.assertEqual(ch.expect('On branch master.*'), 0)

    def test_init_repo_existing(self):
        import os
        os.mkdir('repo1')
        os.chdir('repo1')
        pex.run('git init')
        pex.run('git annex init')

        self.annex = nts.AnnexRepo()
        ch = pex.spawn('git spawn')
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
        self.annex = nts.AnnexRepo(path=None, clone_from='../repo1')

        self.annex = nts.AnnexRepo()
        ch = pex.spawn('git spawn')
        self.assertEqual(ch.expect('On branch master.*'), 0)


@unittest.skip
class AnnexFilesTestCase(unittest.TestCase):
    def setUp(self):
        # noinspection PyGlobalUndefined
        global nts
        import neuroseries as nts
        import os
        # noinspection PyBroadException
        try:
            os.rmdir('scratch/sandbox')
        except:
            pass
        os.makedirs('scratch/sandbox')
        os.chdir('scratch/sandbox')
        # TODO initialize repo

    def tearDown(self):
        import sys
        del sys.modules[nts.__name__]
        del sys.modules[nts.data_manager.__name__]

    def test_add_file(self):
        pass

    def test_add_annex_file(self):
        pass


@unittest.skip
class AnnexRemoteTestCase(unittest.TestCase):
    def setUp(self):
        # noinspection PyGlobalUndefined
        global nts
        import neuroseries as nts
        import os
        # noinspection PyBroadException
        try:
            os.rmdir('scratch/sandbox')
        except:
            pass
        os.makedirs('scratch/sandbox')
        os.chdir('scratch/sandbox')
        # TODO initialize repo

    def tearDown(self):
        import sys
        del sys.modules[nts.__name__]
        del sys.modules[nts.data_manager.__name__]

    def test_add_remote(self):
        pass

    def test_add_special_remote(self):
        pass

    def test_get_existing_file(self):
        pass

    def test_get_missing_file(self):
        pass

    def test_push(self):
        pass

    def test_lookupkey(self):
        pass
