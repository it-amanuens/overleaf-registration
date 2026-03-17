import requests
from bs4 import BeautifulSoup


class Overleaf:
    def __init__(self, instance_url: str):
        self.url = instance_url
        self.session = requests.session()
        self._csrf = None
        self._init_session()

    def _get(self, *args, **kwargs) -> requests.Response:
        return self.session.get(self.url + args[0], *args[1:], **kwargs)

    def _post(self, url, data=None) -> requests.Response:
        self._obtain_csrf()
        url = self.url + url
        if data is None:
            data = {}
        data["_csrf"] = self._csrf
        return self.session.post(url, json=data)

    @staticmethod
    def _ensure_success(response: requests.Response, action: str) -> None:
        if response.status_code >= 400:
            raise RuntimeError(f"failed to {action}: status={response.status_code}")

    def _init_session(self) -> None:
        self._get("/")

    def _obtain_csrf(self) -> str:
        resp: requests.Response = self._get("/login")
        soup = BeautifulSoup(resp.text, "html.parser")
        self._csrf = soup.find("meta", {"name": "ol-csrfToken"})["content"]

    def login(self, email, password) -> None:
        r = self._post("/login", data={
            "email": email,
            "password": password,
        })
        if r.status_code != 200:
            raise ValueError(f"incorrect email or password (status={r.status_code})")

    def logout(self) -> None:
        resp = self._post("/logout")
        self._ensure_success(resp, "logout")

    def register_user(self, email) -> None:
        resp = self._post("/admin/register", data={
            "email": email,
        })
        self._ensure_success(resp, "register user")

    def clear_system_messages(self) -> None:
        resp = self._post("/admin/messages/clear")
        self._ensure_success(resp, "clear system messages")

    def post_system_message(self, content: str) -> None:
        resp = self._post("/admin/messages", data={
            "content": content,
        })
        self._ensure_success(resp, "post system message")
