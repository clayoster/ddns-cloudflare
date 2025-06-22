#!/usr/bin/python3

import ipaddress
import os
from cloudflare import Cloudflare, APIConnectionError, RateLimitError, APIStatusError
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
    return 'badauth'

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
        return 'nohost'

    # Set ip variable
    if 'myip' in request.args:
        ip = request.args.get('myip')
    else:
        log_msg('Incoming request did not contain an IP')
        return 'noip'

    # Verify that the provided IP is valid
    test_ip = is_valid_ip(ip)
    if not test_ip:
        log_msg('The provided IP was not valid: ' + ip)
        return 'invalidip'

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

    # Check if API token is set appropriately
    if api_token not in (None, ''):
        record_name = hostname

        # Initialize the Cloudflare API
        client = Cloudflare(api_token=api_token)

        # Get the DNS zone ID
        zone_id = cloudflare_get_zone_id(client, hostname)

        # Verify fetching zone_id succeeded
        if zone_id is None:
            log_msg('DNS Zone ID was not found. Verify API token is valid and has access to the desired zone')
            return 'apierror_zone_id'

        # Get the DNS record ID
        record_id = cloudflare_get_record_id(client, zone_id, record_name)

        # Verify fetching record_id succeeded
        if record_id is None:
            log_msg('DNS Record ID not found. Verify that the target record exists')
            return 'apierror_record_id'

        # Get the current DNS record details
        record_content, record_ttl_current = cloudflare_get_record_details(client, zone_id, record_id)

        # Verify fetching record_content succeeded
        if record_content is None or record_ttl_current is None:
            log_msg('Error retrieving current record details from API')
            return 'apierror_record_content'

        # Check if the record needs updating
        if record_content != ip or record_ttl_current != record_ttl:
            log_msg('A DNS record update is needed for ' + record_name)

            # Update the record
            response = cloudflare_update_record(client, zone_id, record_id, record_name, ip)

            # Verify updating DNS record succeeded
            if response is None:
                log_msg('The DNS record was not updated successfully')
                return 'apierror_update'

        else:
            log_msg('No update needed for ' + hostname + ' (' + ip + ')')
            response = 'nochg ' + ip
    else:
        log_msg('No api token has been configured for Cloudflare')
        response = 'noapitoken'

    return response

def cloudflare_get_zone_id(client, hostname):
    # Initialize zone ID variable
    zone_id = None

    try:
        zones = client.zones.list()
        for zone in zones:
            if zone.name in hostname:
                zone_id = zone.id
    except (APIConnectionError, RateLimitError, APIStatusError) as e:
        cloudflare_handle_error(e)

    return zone_id

def cloudflare_get_record_id(client, zone_id, record_name):
    # Initialize record ID variable
    record_id = None

    try:
        records = client.dns.records.list(zone_id=zone_id)
        for record in records:
            if record.name == record_name:
                record_id = record.id
    except (APIConnectionError, RateLimitError, APIStatusError) as e:
        cloudflare_handle_error(e)

    return record_id

def cloudflare_get_record_details(client, zone_id, record_id):
    # Initialize variables
    record_content = None
    record_ttl_current = None

    try:
        dns_record = client.dns.records.get(dns_record_id=record_id, zone_id=zone_id)
        # Set variables from the current record data
        record_content = dns_record.content
        record_ttl_current = dns_record.ttl
    except (APIConnectionError, RateLimitError, APIStatusError) as e:
        cloudflare_handle_error(e)

    return record_content, record_ttl_current

def cloudflare_update_record(client, zone_id, record_id, record_name, ip):
    # Initialize variable
    response = None

    try:
        update = client.dns.records.update(zone_id=zone_id, dns_record_id=record_id,
            type=record_type,
            name=record_name,
            content=ip,
            ttl=record_ttl)
        response_name = update.name
        response_content = update.content
    except (APIConnectionError, RateLimitError, APIStatusError) as e:
        cloudflare_handle_error(e)

    if response_name == record_name and response_content == ip:
        log_msg('DNS record updated successfully: ' + record_name + ' (' + ip + ')')
        response = 'good ' + ip

    return response

def cloudflare_handle_error(e):
    if isinstance(e, APIConnectionError):
        print('The Cloudflare API server could not be reached')
        print(e.__cause__)
    elif isinstance(e, RateLimitError):
        print('A 429 status code was received indiciating rate limiting')
    elif isinstance(e, APIStatusError):
        print('A non-200-range status code was received: ' + str(e.status_code))
        print('Response: ' + str(e.response))

def log_msg(msg):
    print(msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
