from pyrogram import Client, filters
from pyrogram.types import Message
import csv
import random
import os
import httpx
import asyncio

PROXY_CSV_FILE = "FILES/proxy.csv"

def load_proxies_from_csv():
    """Load proxies from CSV file"""
    proxies = []
    if not os.path.exists(PROXY_CSV_FILE):
        return proxies
    
    with open(PROXY_CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            proxies.append({
                "host": row.get("host", ""),
                "port": row.get("port", ""),
                "username": row.get("username", ""),
                "password": row.get("password", "")
            })
    return proxies

PROXIES = load_proxies_from_csv()

def get_random_proxy() -> dict:
    """Get a random proxy from the list"""
    if not PROXIES:
        return None
    return random.choice(PROXIES)

def format_proxy(proxy: dict, format_type: str = "url") -> str:
    """Format proxy into different formats"""
    host = proxy["host"]
    port = proxy["port"]
    user = proxy["username"]
    pwd = proxy["password"]
    
    if format_type == "url":
        return f"http://{user}:{pwd}@{host}:{port}"
    elif format_type == "hostport":
        return f"{host}:{port}:{user}:{pwd}"
    elif format_type == "userhost":
        return f"{user}:{pwd}@{host}:{port}"
    return f"{host}:{port}"

async def test_proxy(proxy_url: str) -> tuple:
    """Test if proxy is working"""
    try:
        transport = httpx.AsyncHTTPTransport(proxy=proxy_url)
        async with httpx.AsyncClient(transport=transport, timeout=10) as client:
            res = await client.get("https://ipinfo.io/json")
            if res.status_code == 200:
                data = res.json()
                return True, data.get("ip"), data.get("country", "Unknown")
            return False, None, None
    except Exception as e:
        return False, None, str(e)

# Proxy commands removed as per requirements
# /rproxy, /tproxy, /proxyinfo have been removed
