from dataclasses import dataclass


@dataclass
class AuthSession:
    user_id: str
    access_token: str
    refresh_token: str
    email: str
