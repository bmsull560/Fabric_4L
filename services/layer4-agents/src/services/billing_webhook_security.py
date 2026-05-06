import ipaddress
import os
from fastapi import Request

STRIPE_WEBHOOK_IPS = [
    ipaddress.ip_network("3.18.12.63/32"),
    ipaddress.ip_network("3.130.192.231/32"),
    ipaddress.ip_network("13.235.14.237/32"),
    ipaddress.ip_network("13.235.122.149/32"),
    ipaddress.ip_network("35.154.171.200/32"),
    ipaddress.ip_network("35.154.171.208/32"),
    ipaddress.ip_network("52.15.183.38/32"),
    ipaddress.ip_network("52.15.183.39/32"),
    ipaddress.ip_network("54.88.130.27/32"),
    ipaddress.ip_network("54.88.130.28/32"),
    ipaddress.ip_network("54.187.174.169/32"),
    ipaddress.ip_network("54.187.174.170/32"),
]
STRIPE_WEBHOOK_SKIP_IP_CHECK = os.environ.get("STRIPE_WEBHOOK_SKIP_IP_CHECK", "").lower() in ("true", "1", "yes")


def is_stripe_webhook_ip(client_ip: str) -> bool:
    try:
        ip = ipaddress.ip_address(client_ip)
        if ip.is_loopback:
            return True
        return any(ip in network for network in STRIPE_WEBHOOK_IPS)
    except ValueError:
        return False


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if hasattr(request, "client") and request.client:
        return request.client.host
    return ""
