"""D1-backed cache for scraped search results."""
import os
import json
import time
import requests

_CF_API = "https://api.cloudflare.com/client/v4/accounts/{acc}/d1/database/{db}/query"
_DEFAULT_TTL = 6 * 60 * 60  # 6 hours

_session = requests.Session()


def _config():
    acc = os.environ.get("CF_ACCOUNT_ID", "")
    db = os.environ.get("CF_D1_DATABASE_ID", "")
    token = os.environ.get("CF_API_TOKEN", "")
    if not (acc and db and token):
        return None
    return acc, db, token


def _query(sql, params):
    cfg = _config()
    if not cfg:
        return None
    acc, db, token = cfg
    url = _CF_API.format(acc=acc, db=db)
    try:
        resp = _session.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"sql": sql, "params": params},
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"[cache] D1 returned {resp.status_code}: {resp.text[:200]}")
            return None
        body = resp.json()
        if not body.get("success"):
            print(f"[cache] D1 error: {body.get('errors')}")
            return None
        return body["result"][0]["results"]
    except Exception as e:
        print(f"[cache] D1 request failed: {e}")
        return None


def get_cached(platform, query):
    key = f"{platform}:{query.lower().strip()}"
    rows = _query(
        "SELECT data FROM cache WHERE key = ? AND expires_at > ?",
        [key, int(time.time())],
    )
    if rows:
        try:
            data = json.loads(rows[0]["data"])
            print(f"[cache] HIT {platform} key={key!r}")
            return data
        except (json.JSONDecodeError, KeyError):
            return None
    print(f"[cache] MISS {platform} key={key!r}")
    return None


def set_cached(platform, query, results, ttl=_DEFAULT_TTL):
    if not results:
        return  # don't cache empty results
    key = f"{platform}:{query.lower().strip()}"
    _query(
        "INSERT OR REPLACE INTO cache (key, data, expires_at) VALUES (?, ?, ?)",
        [key, json.dumps(results), int(time.time()) + ttl],
    )
