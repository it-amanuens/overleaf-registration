# Changes 
Most configuration is done in the texts.yaml file. After changing here you recomile the project with docker build and everything should work. 


mer eller mindre fyll i texts.yaml med korrekt information och sen kompilera hela altet med docker compose build, så borde allt funka. 
changes är från 2025-06-08, finns några fler saker som skulle kunna implementeras. 























# Overleaf registration worker (OLD MAIN INFO)

Public user registration for a self-hosted 
[Overleaf](https://github.com/overleaf/overleaf) instance.

### Why?
We are planning to offer a public Overleaf instance to our users (students and teachers), 
but the Community Edition does not support autonomous user registration: only the site
administrator can create users via the admin panel.

This limitation is unacceptable for our use case, so we implemented it ourselves.

### How?
A simple form (available on `/register` path) is offered to the user asking for its email; 
the application then logs into the Overleaf instance with the administrator account
and sends a request to create a user. 

The user can now create an account by clicking the confirmation link on its mailbox.

## Deployment
There is a Docker image available on 
[ghcr.io/studentiunimi/overleaf-registration](https://ghcr.io/studentiunimi/overleaf-registration),
automatically built by GitHub Actions.
You can check the example `docker-compose.yml` file and tweak it with your configuration.

### Environment variables
The Docker container needs all the following environment variables to function properly:

| Environment variable | Description                                          |
|----------------------|------------------------------------------------------|
| `CAPTCHA_SERVER_KEY` | reCAPTCHA v2 server key                              |
| `CAPTCHA_CLIENT_KEY` | reCAPTCHA v2 client key                              |
| `OL_INSTANCE`        | Overleaf self-hosted instance (without trailing `/`) |
| `OL_ADMIN_EMAIL`     | Overleaf administrator account email                 |
| `OL_ADMIN_PASSWORD`  | Overleaf administrator account password              |

## Daily admin system message

This project now supports automatic refresh of the Overleaf admin system message.
The scheduler performs these steps every day:

1. Log in as admin
2. Clear all existing system messages
3. Post `DAILY_SYSTEM_MESSAGE`
4. Log out

### Environment variables

Add these to `.env` (see `example.env`):

| Environment variable      | Description |
|---------------------------|-------------|
| `DAILY_MESSAGE_ENABLED`   | Set to `true` or `false` to enable/disable the daily job |
| `DAILY_SYSTEM_MESSAGE`    | Message text posted daily after clearing existing messages |

### Scheduler behavior

The existing `overleaf-registration` container runs both:

1. `gunicorn` for the `/register` web app
2. A cron job that executes `daily_message_job.py` every day at `06:00` (`Europe/Stockholm`)

### Manual test

Run a one-shot test before relying on the schedule:

```bash
docker compose run --rm overleaf-registration python /daily_message_job.py
```

Then check Overleaf Admin -> System Messages to verify that only the configured message is present.
