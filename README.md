# Chat app with AI agent

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

> TODO: swith to Github Action.

Deploy local repo to GCP:

```
gcloud config set project chat-app-436116

gcloud run deploy chat-app --source .
```