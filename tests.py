import json
import logging
import os
import tempfile
import unittest

from lxml.html.soupparser import fromstring

from flask_migrate import upgrade

# Note: migrate import required although it's not used explicitly
from db import migrate
import website

logging.disable(logging.CRITICAL)

TEST_USERNAME = 'testuser'
TEST_PASSWORD = 'testpass'
TEST_EMAIL = 'testuser@example.com'
EXP_NAME = 'testexp'
EXP_DIMS = [{"name": "x", "dim_type": "linear", "low": 0.0, "high": 1.0}]


class WebsiteTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_fname = tempfile.mkstemp()
        website.app.config['TESTING'] = True
        website.app.config['WTF_CSRF_ENABLED'] = False
        website.app.config['WTF_CSRF_METHODS'] = []
        website.app.config['SQLALCHEMY_DATABASE_URI'] = \
            'sqlite:///{}'.format(self.db_fname)
        self.app = website.app.test_client()
        with website.app.app_context():
            upgrade()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_fname)

    def signup(self, username, password, email):
        return self.app.post('/signup/', data={
            'username': username, 'password': password,
            'email': email}, follow_redirects=True)

    def login(self, username=TEST_USERNAME, password=TEST_PASSWORD):
        return self.app.post('/login', data={
            'username': username, 'password': password
            }, follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def apikey(self):
        # assumes logged-in user
        r = self.app.get('/api/introduction/')
        root = fromstring(r.data)
        apikey = root.find('.//code[@id="auth_token"]') \
            .text_content().strip()
        return apikey

    def create_experiment(self, name=EXP_NAME):
        # assumes logged-in user
        apikey = self.apikey()
        params = {'name': name, 'auth_token': apikey,
                  'dimensions': EXP_DIMS, 'acq_func': 'hedge',
                  'overwrite': False}
        r = self.app.post('/api/create_experiment/',
                          data=json.dumps(params),
                          content_type='application/json')
        return r

    def create_recommendation(self, exp):
        # assumes logged-in user
        apikey = self.apikey()
        params = {'auth_token': apikey, 'experiment_id': exp['id']}
        r = self.app.post('/api/create_recommendation/',
                          data=json.dumps(params),
                          content_type='application/json')
        return r

    def test_index(self):
        r = self.app.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"please login or sign up", r.data)

    def test_signup(self):
        r = self.signup(TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Logout", r.data)

    def test_signup_logout(self):
        r = self.signup(TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Logout", r.data)
        r = self.logout()
        self.assertIn(b"Login", r.data)

    def test_create_experiment(self):
        r = self.signup(TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL)
        r = self.create_experiment()
        self.assertIn(bytes(EXP_NAME, 'utf8'), r.data)
        d = json.loads(r.data)
        self.assertEqual(EXP_NAME, d['name'])
        self.assertEqual(EXP_DIMS, d['dimensions'])

    def test_create_recommendations(self):
        r = self.signup(TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL)
        r = self.create_experiment()
        exp = json.loads(r.data)
        recs = []
        r1 = self.create_recommendation(exp)
        recs.append(json.loads(r1.data))
        r2 = self.create_recommendation(exp)
        recs.append(json.loads(r2.data))
        r3 = self.create_recommendation(exp)
        recs.append(json.loads(r3.data))
        r = self.app.get('/experiment/{}/history/'.format(exp['id']))
        self.assertEqual(r.status_code, 200)
        for rec in recs:
            # TODO: awkward
            x = bytes(str(json.loads(rec['config'])['x']), 'utf8')
            self.assertIn(x, r.data)


if __name__ == '__main__':
    unittest.main()
