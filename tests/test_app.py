import io
import os
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from yolo_detection import paths
from yolo_detection import server
from yolo_detection.server import app

IMAGES = os.path.join(ROOT, 'tests', 'images')


class AppTest(unittest.TestCase):
    """Teste le serveur dans un dossier temporaire : les vraies analyses de data/results ne sont pas touchées."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [mock.patch.object(paths, 'RESULTS', os.path.join(self.tmp.name, 'results')),
                        mock.patch.object(paths, 'SETTINGS', os.path.join(self.tmp.name, 'settings.json'))]
        for p in self.patches:
            p.start()
        os.makedirs(paths.RESULTS)
        self.client = app.test_client()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def analyze(self, image='chien1.jpg', name=None):
        with open(os.path.join(IMAGES, image), 'rb') as f:
            return self.client.post('/detect', data={'image': (f, name or image)}, content_type='multipart/form-data')

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'YOLO Detection', response.data)
        self.assertIn('"dog": "chien"'.encode(), response.data)  # noms français transmis à l'interface

    def test_offline_assets(self):
        for asset in ('/static/app.css', '/static/app.js', '/static/fonts/inter-latin-wght-normal.woff2'):
            response = self.client.get(asset)
            self.assertEqual(response.status_code, 200, asset)
            response.close()
        self.assertNotIn(b'googleapis', self.client.get('/').data)

    def test_detect_creates_analysis(self):
        response = self.analyze(name='Chien été.jpg')
        self.assertEqual(response.status_code, 200)
        record = response.get_json()
        self.assertEqual(record['name'], 'Chien été.jpg')
        self.assertEqual(record['model'], 'yolo26n')
        self.assertIn('dog', [d['class'] for d in record['detections']])
        for filename in ('annotated.jpg', 'thumbnail.jpg', record['original'], 'analysis.json'):
            file = self.client.get(f"/results/{record['id']}/{filename}")
            self.assertEqual(file.status_code, 200, filename)
            file.close()

    def test_same_name_does_not_overwrite(self):
        first = self.analyze().get_json()['id']
        second = self.analyze().get_json()['id']
        self.assertNotEqual(first, second)
        self.assertEqual(len(self.client.get('/history').get_json()), 2)

    def test_history_and_delete(self):
        analysis_id = self.analyze().get_json()['id']
        history = self.client.get('/history').get_json()
        self.assertEqual([h['id'] for h in history], [analysis_id])
        self.assertEqual(history[0]['classes'], [['dog', 1]])
        self.assertEqual(self.client.delete(f'/history/{analysis_id}').status_code, 200)
        self.assertEqual(self.client.get(f'/history/{analysis_id}').status_code, 404)
        self.assertEqual(self.client.get('/history').get_json(), [])

    def test_rejects_unknown_ids(self):
        for url in ('/history/../../yolo_detection', '/results/..%2F..%2Fyolo_detection/server.py',
                    '/history/20260101-000000-zzzz'):
            self.assertEqual(self.client.get(url).status_code, 404, url)

    def test_export_csv(self):
        ids = [self.analyze().get_json()['id'], self.analyze('paris.jpg').get_json()['id']]
        response = self.client.get('/export.csv?ids=' + ','.join(ids + ['20200101-000000-dead']))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['Content-Disposition'])
        lines = response.data.decode('utf-8-sig').strip().split('\r\n')
        self.assertTrue(lines[0].startswith('Analyse;Fichier;Date;Modèle;Objet'))
        self.assertIn(';chien1.jpg;', lines[1])
        self.assertIn(';Chien;dog;', lines[1])
        self.assertIn(';paris.jpg;', lines[2])  # image sans objet : une ligne quand même
        self.assertEqual(len(lines), 3)  # l'identifiant inconnu est ignoré

    def test_detect_rejects_non_image(self):
        response = self.client.post('/detect', data={'image': (io.BytesIO(b'hello'), 'notes.txt')},
                                    content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_detect_rejects_corrupted_image(self):
        response = self.client.post('/detect', data={'image': (io.BytesIO(b'pas une image'), 'faux.jpg')},
                                    content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(os.listdir(paths.RESULTS), [])  # rien ne reste de l'analyse ratée

    def test_detect_without_image(self):
        self.assertEqual(self.client.post('/detect', data={}, content_type='multipart/form-data').status_code, 400)

    def test_settings(self):
        settings = self.client.get('/settings').get_json()
        self.assertEqual(settings['model'], 'yolo26n')
        self.assertEqual([m['id'] for m in settings['models']], ['yolo26n', 'yolo26s', 'yolo26m'])
        self.assertTrue(settings['device'])
        self.assertEqual(self.client.post('/settings', json={'model': 'inconnu'}).status_code, 400)
        with mock.patch.object(server, 'get_model'):  # pas de téléchargement pendant le test
            self.assertEqual(self.client.post('/settings', json={'model': 'yolo26m'}).get_json()['model'], 'yolo26m')
        self.assertEqual(self.client.get('/settings').get_json()['model'], 'yolo26m')

    def test_only_one_webcam_at_a_time(self):
        started, release = threading.Event(), threading.Event()

        def fake_webcam(model):
            started.set()
            release.wait(5)

        with mock.patch.object(server, 'detect_webcam', fake_webcam):
            first = threading.Thread(target=lambda: app.test_client().post('/start-video'))
            first.start()
            started.wait(5)
            second = self.client.post('/start-video')
            release.set()
            first.join()
        self.assertEqual(second.status_code, 409)
        with mock.patch.object(server, 'detect_webcam'):
            self.assertEqual(self.client.post('/start-video').status_code, 200)  # verrou bien relâché


if __name__ == '__main__':
    unittest.main()
