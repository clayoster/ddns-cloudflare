#!/usr/bin/python3

import os
import CloudFlare
from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# Set variables from environment variables
auth_user = os.environ.get('AUTH_USER', None)
auth_pass = os.environ.get('AUTH_PASS', None)
api_token = os.environ.get('API_TOKEN', None)
record_type = os.environ.get('RECORD_TYPE', 'A')
record_ttl = os.environ.get('RECORD_TTL', 60)

users = {
    auth_user: generate_password_hash(auth_pass)
}

@auth.verify_password
def verify_password(username, password): # pylint: disable=inconsistent-return-statements
    if username in users and check_password_hash(users.get(username), password):
        return username

@auth.error_handler
def unauthorized():
    return "badauth"

@app.route('/update')
@auth.login_required
def main():
    # Set hostname variable
    if 'hostname' in request.args:
        hostname = request.args.get('hostname')
    else:
        hostname = 'blank'

    # Set ip variable
    if 'ip' in request.args:
        ip = request.args.get('ip')
    else:
        ip = 'blank'

    # Test inputs to determine the next step
    if hostname == 'blank':
        response = "nohost"
    if ip == 'blank':
        response = "noip"
    else:
        response = check_cloudflare(hostname, ip)

    return response

# Cloudflare Functions
def check_cloudflare(hostname, ip):
    record_name = hostname

    # Determine the DNS zone from the supplied hostname
    hostname_split = hostname.split('.')
    zone_name = '.'.join(hostname_split[1:])

    # Initialize the Cloudflare API
    cf = CloudFlare.CloudFlare(token=api_token)

    # Get the DNS zone ID
    try:
        zones = cf.zones.get(params={'name': zone_name})
        if len(zones) == 0:
            log_msg('Zone not found')
        zone_id = zones[0]['id']
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        log_msg('/zones.get %d %s' % (e, e)) # pylint: disable=bad-string-format-type, consider-using-f-string

    # Get the DNS record ID
    try:
        dns_records = cf.zones.dns_records.get(zone_id, params={'name': record_name, 'type': record_type})
        if len(dns_records) == 0:
            log_msg('DNS record not found')
        record_id = dns_records[0]['id']
        record_content = dns_records[0]['content']
        record_ttl_current = dns_records[0]['ttl']
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        log_msg('/zones.dns_records.get %d %s' % (e, e)) # pylint: disable=bad-string-format-type, consider-using-f-string

    # Test if the record needs updating
    if record_content != ip or record_ttl_current != record_ttl:
        log_msg("A DNS record update is needed for " + record_name)

        # Update the DNS record
        dns_record = {
            'type': record_type,
            'name': record_name,
            'content': ip,
            'ttl': record_ttl
        }

        try:
            cf.zones.dns_records.put(zone_id, record_id, data=dns_record)
            log_msg('DNS record updated successfully: ' + record_name + "(" + ip + ")")
            response = "good " + ip
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            log_msg('/zones.dns_records.put %d %s' % (e, e)) # pylint: disable=bad-string-format-type, consider-using-f-string
            response = "dnserr"
    else:
        response = "nochg " + ip

    return response

def log_msg(msg):
    print(msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
