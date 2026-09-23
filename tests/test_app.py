import io
import os
import sys
import json
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from yolo_detection.server import app, UPLOAD_FOLDER

SAMPLE_IMAGE = os.path.join(ROOT, 'tests', 'images', 'chien1.jpg')
TEST_NAME = 'test_upload'


class AppTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        for suffix in ('.jpg', '_annotated.jpg', '.json'):
            path = os.path.join(UPLOAD_FOLDER, TEST_NAME + suffix)
            if os.path.exists(path):
                os.remove(path)

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'YOLO Detection', response.data)

    def test_detects_dog(self):
        with open(SAMPLE_IMAGE, 'rb') as f:
            response = self.client.post('/', data={'image': (f, TEST_NAME + '.jpg')},
                                        content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'dog', response.data)

        image = self.client.get(f'/results/{TEST_NAME}_annotated.jpg')
        self.assertEqual(image.status_code, 200)
        image.close()
        with open(os.path.join(UPLOAD_FOLDER, TEST_NAME + '.json')) as f:
            classes = [d['class'] for d in json.load(f)]
        self.assertIn('dog', classes)

    def test_detect_api(self):
        with open(SAMPLE_IMAGE, 'rb') as f:
            response = self.client.post('/detect', data={'image': (f, TEST_NAME + '.jpg')},
                                        content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['annotated'], TEST_NAME + '_annotated.jpg')
        dog = next(d for d in data['detections'] if d['class'] == 'dog')
        self.assertRegex(dog['color'], r'^#[0-9a-f]{6}$')

    def test_detect_rejects_non_image(self):
        response = self.client.post('/detect', data={'image': (io.BytesIO(b'hello'), 'notes.txt')},
                                    content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_post_without_image(self):
        response = self.client.post('/', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
