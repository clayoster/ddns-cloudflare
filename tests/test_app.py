import base64
import os

def test_env_vars():
    assert os.environ["AUTH_USER"] == "testuser"
    assert os.environ["AUTH_PASS"] == "testpass"

def basic_auth(username, password):
    credentials = f"{username}:{password}"
    auth_header = base64.b64encode(credentials.encode()).decode('utf-8')
    return {'Authorization': f'Basic {auth_header}'}

def test_good_auth(app, client):
    auth_headers = basic_auth('testuser', 'testpass')
    res = client.get('/nic/update?hostname=test.domain.com&myip=0.0.0.0', headers=auth_headers)
    assert b'noapitoken' in res.data
    assert res.status_code == 200

def test_bad_auth(app, client):
    auth_headers = basic_auth('testuser', 'badpass')
    res = client.get('/nic/update?hostname=test.domain.com&myip=0.0.0.0', headers=auth_headers)
    assert b'badauth' in res.data
    assert res.status_code == 401


def test_missing_hostname(app, client):
    auth_headers = basic_auth('testuser', 'testpass')
    res = client.get('/nic/update?myip=0.0.0.0', headers=auth_headers)
    assert b'nohost' in res.data
    assert res.status_code == 200

def test_missing_ip(app, client):
    auth_headers = basic_auth('testuser', 'testpass')
    res = client.get('/nic/update?hostname=test.domain.com', headers=auth_headers)
    assert b'noip' in res.data
    assert res.status_code == 200
