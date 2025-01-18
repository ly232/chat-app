# Chat app with AI agent

## Overview

A chat app that leverages gRPC's bi-di streaming capability to broadcast to all
online clients.

For MVP, the intended use case is limited to a small group of users (e.g. <10).
For example, family members + AI agents or

## Architectural decisions

### gRPC vs. Web Socket

Unlike a typical chat app where it heavily leverages web sockets, this chat app
intentionally uses gRPC bi-di streaming for the following reasons:

1.  Language-agnostic stub codegen helps to reduce boilerplates.
2.  Transferring protobuf rather than json requires less network bandwidth.
3.  Protobuf enforces strong typing.

### Database choice

### Message causality

## Local development

Local setup:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Start server:

```
python chat_server_main.py
```

Start client:

```
# Terminal 1:
python -m client.chat_client

# Terminal 2:
python -m client.chat_client
```

## Production usage

Chat server is deployed in GCP at https://console.cloud.google.com/run?project=chat-app-436116. You may connect to it via:

```
python -m client.chat_client --remote=1
```

## Security

SSL/TLS establishes a trusted channel between client and server. Normally for browser-based apps, it's recommended to have a trusted CA issue the cert. But (a) it costs money, and (b) in this chat app, both client and server are self-owned and client is a commandline tool. So we'll opt for a self-served SSL/TLS generated cert. Setting up SSL/TLS enables e2e encryption to protect against man-in-the-middle attacks.

```
# Generate a private key
openssl genpkey -algorithm RSA -out server.key -aes256

# To remove password:
openssl rsa -in server.key -out server.key

# Generate a certificate signing request (CSR)
# Remember to set:
# Common Name (e.g. server FQDN or YOUR name) []:localhost
openssl req -new -key server.key -out server.csr

# Create the self-signed certificate
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
```

## CI/CD

`git push -u origin main` will trigger a Cloud Build.

Deploy local repo to GCP:

```
gcloud config set project chat-app-436116

gcloud run deploy chat-app --source .
```

## Future ideas

### Features

*  AI agent integration.
*  Message history.
*  Access control.
*  Mobile app & web app.
*  Multi-media support.

### Infrastructure

*  GitHub Action for CI/CD.
*  Kubernetes migration.
*  Prober test.
*  Load test.
