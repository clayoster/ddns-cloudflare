# ddns-cloudflare

This is a self-hosted DDNS service for receiving public IP updates from a router or other local source and updating a DNS record in Cloudflare.

The primary purposes for building yet another DDNS tool for updating Cloudflare records:
- Many other solutions depend upon using a `Global` API token which is unacceptable for this singular purpose. This solution allows the use of a API token scoped with privileges to edit a single DNS zone.
  - Unforunately Cloudflare does not allow limiting the edit privileges to a single DNS record in a zone at this point.
- Self-hosted option for receving DDNS updates from a router or other local source rather than depending on querying an external API for public IP address changes

Valid response codes were gathered from here:\
  https://help.dyn.com/remote-access-api \
  https://github.com/troglobit/inadyn/blob/master/plugins/common.c

Manual updates can be sent to this service with a GET request in the following format: \
`https://<username>:<password>@ddns.example.com/nic/update?hostname=<dns record to update>&myip=<public ip>`

Note that this can use a "scoped" CloudFlare API Token

# Deployment with Docker Compose (Recommended)

*Note: The application requires authentication to be configure via the AUTH_USER and AUTH_PASS environment variables. Without those set, the app will fail to start successfully which is intentional.*

#### Example docker-compose.yml file

```
version: '3.4'
services:
  ddns-cloudflare:
    container_name: ddns-cloudflare
    image: ghcr.io/clayoster/test-ddns-cloudflare:0.1.0
    restart: always
    environment:
      # Username for authenticating to the ddns service
      - AUTH_USER=<auth username>
      # Password for authenticating to the ddns service
      - AUTH_PASS=<auth password>
      # Your CloudFlare API token with access to the necessary DNS Zone
      - API_TOKEN=<cloudflare api token>
    ports:
        - "8080:8080"
```

## To-Dos
- Make "hostname" compatible with accepting up to 20 comma-delimited domain names
- Upgrade python-cloudflare dependency to version 3 and complete corresponding rewrite
