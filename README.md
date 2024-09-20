# ddns-cloudflare

Self-hosted DDNS service for receiving public IP updates from a router or other local source
and updating a DNS record in Cloudflare.

The primary purposes for building yet another DDNS tool for updating Cloudflare records:
- Many other solutions depend upon using a `Global` API token which is unacceptable for this singular purpose. This solution allows the use of a API token scoped with privileges to edit a single DNS zone.
  - Unforunately Cloudflare does not allow limiting the edit privileges to a single DNS record in a zone at this point.
- Self-hosted option for receving DDNS updates from a router or other local source rather than depending on querying an external API for public IP address changes

Valid response codes were gathered from here:\
  https://help.dyn.com/remote-access-api/\
  https://github.com/troglobit/inadyn/blob/master/plugins/common.c

This service requires a GET request in the following format
  
    https://<username>:<password>@ddns.example.com/nic/update?hostname=<dns record to update>&myip=<public ip>
