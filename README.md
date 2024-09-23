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
