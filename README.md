# ddns-cloudflare

This is a self-hosted DDNS service for receiving public IP updates from a router or other local source and updating a DNS record in Cloudflare.

Container images are based on Alpine Linux and are available for these platforms:
  - linux/amd64
  - linux/arm64
  - linux/arm/v6
  - linux/arm/v7

---

The primary reasons for building *yet another* DDNS tool for updating Cloudflare records:
- Many other solutions depend upon using a ***Global*** API token which is unacceptable for this singular purpose. This solution allows the use of a API token scoped with privileges to edit a single DNS zone.
  - Unfortunately Cloudflare does not allow limiting the edit privileges to a single DNS record in a zone at this point.
- Self-hosted option for receiving DDNS updates from a router or other local source rather than depending on an external service for detecting public IP address changes

---

Valid response codes were gathered from here:\
  https://help.dyn.com/remote-access-api \
  https://github.com/troglobit/inadyn/blob/master/plugins/common.c

## How to send DDNS Updates to this Application

Example information that will be used below:
- Cloudflare Record to Update: `home.example.com`
- Cloudflare API token (scoped to a single DNS Zone!): `supersecretapitoken`
- Username for the ddns-cloudflare service: `ddns-user`
- Password for the ddns-cloudflare service: `ddns-password`
- Server running the ddns-cloudflare service: `ddns.example.com:8080`
  - Port 8080 can be dropped by running the application behind a reverse proxy

### Sending updates from a router (Using a Unifi Dream Machine as an example)
- Service: `dyndns`
- Hostname: `home.example.com`
- Username: `ddns-user`
- Password: `ddns-password`
- Server: `ddns.example.com:8080/nic/update?hostname=%h&myip=%i`

### Manual updates can be sent to this service with a GET request in the following format:

```
curl "http://ddns-user:ddns-password@ddns.example.com:8080/nic/update?hostname=home.example.com&myip=0.0.0.0"
```

## Deployment Options

### Docker Compose (Recommended)

*Note: The application requires authentication to be configure via the AUTH_USER and AUTH_PASS environment variables. Without those set, the app will fail to start successfully which is intentional.*

#### Example docker-compose.yml file

```yaml
services:
  ddns-cloudflare:
    container_name: ddns-cloudflare
    # Using 'latest' as an example. specifying a specific version is preferred
    image: ghcr.io/clayoster/ddns-cloudflare:latest
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

### Kubernetes

Example Kubernetes manifest file defining the following items:
- Namespace
- Secret
- Deployment (A single pod with health checks)
- Service
- Ingress (Configured for nginx ingress with example domain "ddns.example.com")

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: ddns-cloudflare
---
apiVersion: v1
kind: Secret
metadata:
    name: ddns-cloudflare
    namespace: ddns-cloudflare
type: Opaque
stringData:
    # Encrypt with SOPS or a similar tool
    AUTH_USER: ddns-user
    AUTH_PASS: ddns-password
    API_TOKEN: supersecretapitoken
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ddns-cloudflare
  namespace: ddns-cloudflare
  labels:
    app: ddns-cloudflare
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ddns-cloudflare
  template:
    metadata:
      labels:
        app: ddns-cloudflare
    spec:
      containers:
      - name: ddns-cloudflare
        image: ghcr.io/clayoster/ddns-cloudflare:latest
        env:
        - name: AUTH_USER
          valueFrom:
            secretKeyRef:
              name: ddns-cloudflare
              key: AUTH_USER
        - name: AUTH_PASS
          valueFrom:
            secretKeyRef:
              name: ddns-cloudflare
              key: AUTH_PASS
        - name: API_TOKEN
          valueFrom:
            secretKeyRef:
              name: ddns-cloudflare
              key: API_TOKEN
        ports:
          - containerPort: 8080
            name: 8080tcp
            protocol: TCP
        resources: {}
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 30
          successThreshold: 1
          timeoutSeconds: 3
          failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: ddns-cloudflare
  namespace: ddns-cloudflare
spec:
  selector:
    app: ddns-cloudflare
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ddns-cloudflare
  namespace: ddns-cloudflare
spec:
  ingressClassName: nginx
  rules:
  - host: ddns.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ddns-cloudflare
            port:
              number: 80
```

Optionally, you can deploy an inadyn pod to send updates into to the ddns-cloudflare pod

- inadyn configuration file defined within a secret
- Deployment (A single pod with health checks)
  - Mounts the secret as a file /etc/inadyn/inadyn.conf

```yaml
apiVersion: v1
kind: Secret
metadata:
    name: inadyn-config
    namespace: ddns-cloudflare
type: Opaque
stringData:
    # Encrypt with SOPS or a similar tool
    inadyn.conf: |-
        custom home.example.com:1 {
            hostname = "home.example.com"
            username = "ddns-user"
            password = "ddns-password"
            ddns-server = "ddns.example.com"
            ddns-path = "/nic/update?hostname=%h&myip=%i"
        }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inadyn
  namespace: ddns-cloudflare
spec:
  replicas: 1
  selector:
    matchLabels:
      app: inadyn
  template:
    metadata:
      labels:
        app: inadyn
    spec:
      containers:
        - name: inadyn
          image: troglobit/inadyn:v2.13.0
          args: ["--config", "/etc/inadyn/inadyn.conf"]
          volumeMounts:
            - name: inadyn-config
              mountPath: /etc/inadyn
              readOnly: true
      volumes:
        - name: inadyn-config
          secret:
            secretName: inadyn-config
```
---
Additional recommendations:
- Only run this container on an internal network and not exposed to the internet
- Run this behind a reverse proxy with HTTPS configured to keep requests encrypted

## To-Dos
- Make "hostname" compatible with accepting up to 20 comma-delimited domain names
