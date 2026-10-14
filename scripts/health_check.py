#!/usr/bin/env python3
"""Health check with retry: exit 0 if the app answers healthy, 1 otherwise."""
import json
import sys
import time
import urllib.request


def check(url, timeout=3):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            body = json.load(resp)
            return body.get("status") == "healthy"
    except Exception as exc:
        print(f"  not ready: {exc}")
        return False


def main():
    if len(sys.argv) < 2:
        print("usage: health_check.py URL [retries] [delay_seconds]")
        return 2
    url = sys.argv[1]
    retries = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    delay = float(sys.argv[3]) if len(sys.argv) > 3 else 3

    for attempt in range(1, retries + 1):
        print(f"Attempt {attempt}/{retries}: GET {url}")
        if check(url):
            print("Health check passed")
            return 0
        time.sleep(delay)

    print(f"Health check failed after {retries} attempts")
    return 1


if __name__ == "__main__":
    sys.exit(main())
