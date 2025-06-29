import base64
import os
import subprocess

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
    assert res.status_code == 400

def test_missing_ip(app, client):
    auth_headers = basic_auth('testuser', 'testpass')
    res = client.get('/nic/update?hostname=test.domain.com', headers=auth_headers)
    assert b'noip' in res.data
    assert res.status_code == 400

def test_bad_ip(app, client):
    auth_headers = basic_auth('testuser', 'testpass')
    res = client.get('/nic/update?hostname=test.domain.com&myip=0.0.0.', headers=auth_headers)
    assert b'invalidip' in res.data
    assert res.status_code == 400

def test_healthcheck(app, client):
    res = client.get('/health')
    assert b'healthy' in res.data
    assert res.status_code == 200

def test_bareurl(app, client):
    res = client.get('/')
    assert b'Requests need to be made to /nic/update /update' in res.data
    assert res.status_code == 400

def test_without_auth_variables(monkeypatch):
    monkeypatch.delenv("AUTH_USER", raising=False)
    monkeypatch.delenv("AUTH_PASS", raising=False)

    result = subprocess.run(["python3", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )

    # Confirm the application fails to start without AUTH_USER and AUTH_PASS set
    assert result.returncode != 0
    assert b'Authentication is not configured' in result.stdout
