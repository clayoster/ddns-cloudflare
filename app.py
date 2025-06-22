#!/usr/bin/python3

import ipaddress
import os
import cloudflare
from cloudflare import Cloudflare
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
    log_msg('Authentication failed')
    return "badauth"

@app.route('/update')
@app.route('/nic/update')
@auth.login_required
def main():
    # Initialize variables
    hostname = None
    ip = None

    # Set hostname variable
    if 'hostname' in request.args:
        hostname = request.args.get('hostname')
    else:
        log_msg('The incoming request did not contain a hostname')
        return "nohost"

    # Set ip variable
    if 'myip' in request.args:
        ip = request.args.get('myip')
    else:
        log_msg('Incoming request did not contain an IP')
        return "noip"

    # Verify that the provided IP is valid
    test_ip = is_valid_ip(ip)
    if not test_ip:
        log_msg('The provided IP was not valid: ' + ip)
        return "invalidip"

    log_msg('Received update request for ' + hostname + ' (' + ip + ')')
    response = check_cloudflare(hostname, ip)

    return response

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

# Cloudflare Functions
def check_cloudflare(hostname, ip):
    # Initialize record and zone ID variables
    record_id = None
    zone_id = None

    # Check if API token is set appropriately
    if api_token not in (None, ''):
        record_name = hostname

        # Initialize the Cloudflare API
        client = Cloudflare(api_token=api_token)

        # Get the DNS zone ID
        try:
            zones = client.zones.list()
            for zone in zones:
                print(zone.name)
                #if zone.name == zone_name:
                if zone.name in hostname:
                    zone_id = zone.id
        except cloudflare.APIConnectionError as e:
            log_msg('/zones.get %d %s' % (e, e)) # pylint: disable=bad-string-format-type, consider-using-f-string

        # Get the DNS record ID
        try:
            records = client.dns.records.list(zone_id=zone_id)
            for record in records:
                if record.name == record_name:
                    record_id = record.id
        except cloudflare.APIConnectionError as e:
            log_msg('/zones.dns_records.get %d %s' % (e, e)) # pylint: disable=bad-string-format-type, consider-using-f-string

        # Get the current DNS record
        try:
            dns_record = client.dns.records.get(dns_record_id=record_id, zone_id=zone_id)
            # Set variables from the current record data
            record_content = dns_record.content
            record_ttl_current = dns_record.ttl
        except cloudflare.APIConnectionError as e:
            log_msg('/zones.dns_records.get %d %s' % (e, e)) # pylint: disable=bad-string-format-type, consider-using-f-string

        # Test if the record needs updating
        if record_content != ip or record_ttl_current != record_ttl:
            log_msg("A DNS record update is needed for " + record_name)

            # Update the record
            try:
                client.dns.records.update(zone_id=zone_id, dns_record_id=record_id,
                    type=record_type,
                    name=record_name,
                    content=ip,
                    ttl=record_ttl)
                log_msg('DNS record updated successfully: ' + record_name + ' (' + ip + ')')
                response = "good " + ip
            except cloudflare.APIConnectionError as e:
                log_msg('/zones.dns_records.put %d %s' % (e, e)) # pylint: disable=bad-string-format-type, consider-using-f-string
                response = "dnserr"
        else:
            log_msg('No update needed for ' + hostname + ' (' + ip + ')')
            response = "nochg " + ip
    else:
        log_msg('No api token has been configured for Cloudflare')
        response = "noapitoken"

    return response

def log_msg(msg):
    print(msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
