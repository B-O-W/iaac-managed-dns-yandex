#!/usr/bin/env python3
import os
import yaml
import requests

API_BASE = "https://api.cloudflare.com/client/v4"

def load_records(path="records.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f).get("records", [])

def main():
    token   = os.getenv("CLOUDFLARE_API_TOKEN")
    zone_id = os.getenv("ZONE_ID")
    if not token or not zone_id:
        raise RuntimeError("CLOUDFLARE_API_TOKEN and ZONE_ID must be set")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    # Fetch zone details
    resp = requests.get(f"{API_BASE}/zones/{zone_id}", headers=headers)
    resp.raise_for_status()
    zone_name = resp.json()["result"]["name"]

    # Fetch existing DNS records (up to 1000)
    resp = requests.get(f"{API_BASE}/zones/{zone_id}/dns_records?per_page=1000",
                        headers=headers)
    resp.raise_for_status()
    existing = {}
    for rec in resp.json()["result"]:
        existing.setdefault(rec["name"], []).append(rec)

    desired = load_records()
    ns_target = "ns1.yandexcloud.kz"
    ttl       = 3600

    # 1) Create/update/convert NS records
    for rec in desired:
        sub = rec["name"]
        full = sub if sub.endswith(zone_name) else f"{sub}.{zone_name}"
        payload = {
            "type":    "NS",
            "name":    full,
            "content": ns_target,
            "ttl":     ttl,
            "comment": "proxied to yandex dns"
        }

        items = existing.get(full, [])
        # Update existing NS
        ns_rec = next((r for r in items if r["type"] == "NS"), None)
        if ns_rec:
            if ns_rec["content"] != ns_target:
                print(f"↻ Updating NS for {full}")
                requests.put(
                    f"{API_BASE}/zones/{zone_id}/dns_records/{ns_rec['id']}",
                    headers=headers, json=payload
                ).raise_for_status()
            else:
                print(f"✔ NS for {full} OK")
            continue

        # Convert A→NS
        a_rec = next((r for r in items if r["type"] == "A"), None)
        if a_rec:
            print(f"↻ Converting A→NS for {full}")
            requests.put(
                f"{API_BASE}/zones/{zone_id}/dns_records/{a_rec['id']}",
                headers=headers, json=payload
            ).raise_for_status()
            continue

        # Create new NS
        print(f"➕ Creating NS for {full}")
        requests.post(
            f"{API_BASE}/zones/{zone_id}/dns_records",
            headers=headers, json=payload
        ).raise_for_status()

    # 2) Delete obsolete NS records
    desired_set = {
        r["name"] if r["name"].endswith(zone_name) else f"{r['name']}.{zone_name}"
        for r in desired
    }
    for name, recs in existing.items():
        for r in recs:
            if r["type"] == "NS" and name not in desired_set:
                print(f"🗑 Deleting obsolete NS for {name}")
                requests.delete(
                    f"{API_BASE}/zones/{zone_id}/dns_records/{r['id']}",
                    headers=headers
                ).raise_for_status()

    print("✅ NS synchronization complete")

if __name__ == "__main__":
    main()
