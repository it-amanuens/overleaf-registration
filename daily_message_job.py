import logging
import os
import sys

import overleaf


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - daily-message-job - %(message)s",
)


def _as_bool(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"missing required environment variable: {name}")
    return value


def main() -> int:
    enabled = _as_bool(os.environ.get("DAILY_MESSAGE_ENABLED"), default=True)
    if not enabled:
        logging.info("Daily message job is disabled by DAILY_MESSAGE_ENABLED=false")
        return 0

    instance = _required_env("OL_INSTANCE")
    admin_email = _required_env("OL_ADMIN_EMAIL")
    admin_password = _required_env("OL_ADMIN_PASSWORD")
    message = _required_env("DAILY_SYSTEM_MESSAGE")

    client = overleaf.Overleaf(instance)
    logged_in = False

    try:
        logging.info("Starting daily system message refresh")
        client.login(admin_email, admin_password)
        logged_in = True
        client.clear_system_messages()
        client.post_system_message(message)
        logging.info("Daily system message refresh completed successfully")
        return 0
    except Exception as exc:
        logging.error("Daily system message refresh failed: %s", exc)
        return 1
    finally:
        if logged_in:
            try:
                client.logout()
            except Exception as exc:
                logging.warning("Logout failed after job run: %s", exc)


if __name__ == "__main__":
    sys.exit(main())
