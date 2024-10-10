# ddns-cloudflare

This is a self-hosted DDNS service for receiving public IP updates from a router or other local source and updating a DNS record in Cloudflare.

The primary purposes for building yet another DDNS tool for updating Cloudflare records:
- Many other solutions depend upon using a `Global` API token which is unacceptable for this singular purpose. This solution allows the use of a API token scoped with privileges to edit a single DNS zone.
  - Unforunately Cloudflare does not allow limiting the edit privileges to a single DNS record in a zone at this point.
- Self-hosted option for receving DDNS updates from a router or other local source rather than depending on querying an external API for public IP address changes

Valid response codes were gathered from here:\
  https://help.dyn.com/remote-access-api \
  https://github.com/troglobit/inadyn/blob/master/plugins/common.c

## How to send DDNS Updates to this Application

Example information that will be used below:
- Cloudflare Record to Update: `home.example.com`
- Cloudflare API token (scoped to a single DNS Zone!): `supersecretapitoken`
- Username for the ddns-cloudflare service: `ddns-user`
- Password for the ddns-cloudflare service: `ddns-password`
- Server running the ddns-cloudflare service: `ddns.example.com`

### Sending updates from a router (Using a Unifi Dream Machine as an example)
- Service: `dyndns`
- Hostname: `home.example.com`
- Username: `ddns-user`
- Password: `ddns-password`
- Server: `ddns.example.com/update?hostname=%h&myip=%i`

### Manual updates can be sent to this service with a GET request in the following format:

```
curl http://ddns-user:ddns-password@ddns.example.com:8080/nic/update?hostname=home.example.com&myip=0.0.0.0
```

## Deployment with Docker Compose (Recommended)

*Note: The application requires authentication to be configure via the AUTH_USER and AUTH_PASS environment variables. Without those set, the app will fail to start successfully which is intentional.*

#### Example docker-compose.yml file

```
version: '3.4'
services:
  ddns-cloudflare:
    container_name: ddns-cloudflare
    # Using 'latest' as an example. specifying a specific version is preferred
    image: ghcr.io/clayoster/test-ddns-cloudflare:latest
    restart: always
    environment:
      # Username for authenticating to the ddns service
      - AUTH_USER=ddns-user
      # Password for authenticating to the ddns service
      - AUTH_PASS=ddns-password
      # Your CloudFlare API token with access to the necessary DNS Zone
      - API_TOKEN=supersecretapitoken
    ports:
        - "8080:8080"
```

Additional recommendations:
- Only run this container on an internal network and not exposed to the internet
- Run this behind a reverse proxy with HTTPS configured to keep requests encrypted

## To-Dos
- Make "hostname" compatible with accepting up to 20 comma-delimited domain names
- Upgrade python-cloudflare dependency to version 3 and complete corresponding rewrite
