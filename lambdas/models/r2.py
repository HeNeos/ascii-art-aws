from dataclasses import dataclass


@dataclass
class R2Credentials:
    cloudflare_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    ascii_art_bucket_name: str
