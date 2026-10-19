import importlib.util
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest import mock

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parents[1]
TEST_TMP_ROOT = ROOT / '.test-temp'
TEST_TMP_ROOT.mkdir(exist_ok=True)
TEST_PASSWORD = 'private-test-password'
TEST_CONFIG = {
    'FLASK_SECRET_KEY': 'test-only-signing-key-' + 'x' * 40,
    'ADMIN_EMAIL': 'owner@example.test',
    'ADMIN_PASSWORD_HASH': generate_password_hash(TEST_PASSWORD, method='pbkdf2:sha256:1000'),
    'APP_ENV': 'development',
}


def csrf_token(response):
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    if not match:
        raise AssertionError('CSRF token missing from form')
    return match.group(1).decode('ascii')


class SecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chatbot_stub = ModuleType('src.chatbot')
        chatbot_stub.get_rag_response = lambda question: '<strong>Safe answer</strong>'
        chatbot_stub.add_document_to_database = lambda filepath, filename: {
            'success': True, 'chunks': 1, 'error': None,
        }
        chatbot_stub.delete_document_from_database = lambda filename: {
            'success': True, 'deleted_chunks': 1, 'error': None,
        }
        spec = importlib.util.spec_from_file_location('security_test_app', ROOT / 'app.py')
        cls.application = importlib.util.module_from_spec(spec)
        with mock.patch.dict(os.environ, TEST_CONFIG), mock.patch.dict(
            sys.modules, {'src.chatbot': chatbot_stub}
        ):
            spec.loader.exec_module(cls.application)
        cls.application.app.config['TESTING'] = True

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT)
        self.previous_upload_folder = self.application.UPLOAD_FOLDER
        self.application.UPLOAD_FOLDER = self.temp_directory.name
        self.application.app.config['UPLOAD_FOLDER'] = self.temp_directory.name
        self.client = self.application.app.test_client()

    def tearDown(self):
        self.application.UPLOAD_FOLDER = self.previous_upload_folder
        self.application.app.config['UPLOAD_FOLDER'] = self.previous_upload_folder
        self.temp_directory.cleanup()

    def login(self, password=TEST_PASSWORD):
        token = csrf_token(self.client.get('/admin/login'))
        return self.client.post('/admin/login', data={
            'email': TEST_CONFIG['ADMIN_EMAIL'],
            'password': password,
            'csrf_token': token,
        })

    def test_valid_login_and_cookie_policy(self):
        response = self.login()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/admin')
        self.assertEqual(self.client.get('/admin').status_code, 200)
        cookie = response.headers['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Lax', cookie)
        self.assertNotIn(' Secure;', cookie)
        self.assertFalse(self.application.app.config['SESSION_COOKIE_SECURE'])

    def test_invalid_credentials_rejected(self):
        response = self.login(password='wrong-password')
        self.assertEqual(response.status_code, 200)
        self.assertIn('không đúng'.encode('utf-8'), response.data)
        self.assertEqual(self.client.get('/admin').status_code, 302)

    def test_csrf_invalid_admin_requests_rejected(self):
        self.assertEqual(self.client.post('/admin/login', data={
            'email': TEST_CONFIG['ADMIN_EMAIL'], 'password': TEST_PASSWORD,
        }).status_code, 400)
        self.login()
        with mock.patch.object(self.application, 'add_document_to_database') as add, mock.patch.object(
            self.application, 'delete_document_from_database'
        ) as delete:
            upload = self.client.post('/admin', data={
                'file': (io.BytesIO(b'hello'), 'blocked.txt'),
            })
            removal = self.client.post('/admin/delete/blocked.txt', data={'csrf_token': 'wrong'})
            self.assertEqual(upload.status_code, 400)
            self.assertEqual(removal.status_code, 400)
            add.assert_not_called()
            delete.assert_not_called()
        self.assertFalse((Path(self.temp_directory.name) / 'blocked.txt').exists())

    def test_upload_and_delete_still_work_with_csrf(self):
        self.login()
        token = csrf_token(self.client.get('/admin'))
        with mock.patch.object(self.application, 'add_document_to_database', return_value={
            'success': True, 'chunks': 1, 'error': None,
        }) as add:
            response = self.client.post('/admin', data={
                'csrf_token': token,
                'file': (io.BytesIO('Tuyển sinh PTIT'.encode('utf-8')), 'security-test.txt'),
            }, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 200)
            add.assert_called_once()
        uploaded = Path(self.temp_directory.name) / 'security-test.txt'
        self.assertTrue(uploaded.exists())

        token = csrf_token(self.client.get('/admin'))
        with mock.patch.object(self.application, 'delete_document_from_database', return_value={
            'success': True, 'deleted_chunks': 1, 'error': None,
        }) as delete:
            response = self.client.post('/admin/delete/security-test.txt', data={'csrf_token': token})
            self.assertEqual(response.status_code, 302)
            delete.assert_called_once_with('security-test.txt')
        self.assertFalse(uploaded.exists())

    def test_chat_remains_public_without_csrf(self):
        with mock.patch.object(self.application, 'get_rag_response', return_value='<p>answer</p>'):
            response = self.client.post('/chat', json={'message': 'Question'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'response': '<p>answer</p>'})

    def test_server_defaults_to_local_and_no_debug(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.application.get_server_options(), {
                'host': '127.0.0.1', 'port': 5000, 'debug': False,
            })
        with mock.patch.dict(os.environ, {'FLASK_HOST': '0.0.0.0', 'FLASK_DEBUG': '1'}):
            self.assertFalse(self.application.get_server_options()['debug'])

    def test_missing_security_configuration_fails_before_chatbot_import(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT) as empty_directory:
            environment = os.environ.copy()
            for name in ('FLASK_SECRET_KEY', 'ADMIN_EMAIL', 'ADMIN_PASSWORD_HASH'):
                environment.pop(name, None)
            environment['PYTHONPATH'] = str(ROOT)
            result = subprocess.run(
                [sys.executable, '-c', 'import app'],
                cwd=empty_directory,
                env=environment,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FLASK_SECRET_KEY', result.stderr)

    def test_https_environment_requires_secure_cookie(self):
        script = '''
import sys
from types import ModuleType
stub = ModuleType('src.chatbot')
stub.get_rag_response = lambda question: ''
stub.add_document_to_database = lambda filepath, filename: {}
stub.delete_document_from_database = lambda filename: {}
sys.modules['src.chatbot'] = stub
import app
print(app.app.config['SESSION_COOKIE_SECURE'])
'''
        with tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT) as empty_directory:
            environment = os.environ.copy()
            environment.update(TEST_CONFIG)
            environment['APP_ENV'] = 'production'
            environment['PYTHONPATH'] = str(ROOT)
            result = subprocess.run(
                [sys.executable, '-c', script],
                cwd=empty_directory,
                env=environment,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'True')


if __name__ == '__main__':
    unittest.main()
