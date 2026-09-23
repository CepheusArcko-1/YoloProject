import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from yolo_detection import uninstall


class UninstallTest(unittest.TestCase):
    """Vérifie sur un faux projet que seuls les éléments installés sont listés et supprimés."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.write('.venv/pyvenv.cfg', 'home = x')
        self.write('.venv/Lib/site-packages/paquet.py', 'x' * 100)
        self.write('data/models/yolo26n.pt', 'modele')
        self.write('data/logs/installation.log', 'log')
        self.write('yolo_detection/__pycache__/server.cpython.pyc', 'x')
        # À conserver
        self.write('yolo_detection/server.py', 'code')
        self.write('YOLO Detection.exe', 'exe')
        self.write('data/results/mon_image.jpg', 'resultat')
        self.write('tests/test_app.py', 'test')

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, relative, content):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)

    def test_lists_only_installed_items(self):
        paths = {os.path.relpath(path, self.root) for _, path, _ in uninstall.find_items(self.root)}
        # Le raccourci du Bureau pointe vers le vrai projet, pas vers ce faux projet : il n'est pas listé
        self.assertEqual(paths, {'.venv', os.path.join('data', 'models'), os.path.join('data', 'logs'),
                                 os.path.join('yolo_detection', '__pycache__')})

    def test_remove_keeps_project_and_results(self):
        for _, path, _ in uninstall.find_items(self.root):
            uninstall.remove(path)
        remaining = sorted(os.path.relpath(os.path.join(folder, name), self.root)
                           for folder, _, files in os.walk(self.root) for name in files)
        self.assertEqual(remaining, sorted([os.path.join('yolo_detection', 'server.py'), 'YOLO Detection.exe',
                                            os.path.join('data', 'results', 'mon_image.jpg'),
                                            os.path.join('tests', 'test_app.py')]))

    def test_venv_without_pyvenv_cfg_is_ignored(self):
        os.remove(os.path.join(self.root, '.venv', 'pyvenv.cfg'))
        paths = {os.path.relpath(path, self.root) for _, path, _ in uninstall.find_items(self.root)}
        self.assertNotIn('.venv', paths)

    def test_format_size(self):
        self.assertEqual(uninstall.format_size(796), '796 octets')
        self.assertEqual(uninstall.format_size(5 * 1024 * 1024 + 300 * 1024), '5,3 Mo')


if __name__ == '__main__':
    unittest.main()
