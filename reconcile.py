"""Payment reconciliation.
Reads payments.jsonl and works out how much money we actually collected.
Run:  python reconcile.py
"""
import json
import os
import requests

# --- AUTOMATIC FILE DOWNLOADER ---
def download_file(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading {filename}...")
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

download_file("https://raw.githubusercontent.com/quadri40/koya-payment-reconciliation/main/payments.jsonl", "payments.jsonl")
download_file("https://raw.githubusercontent.com/quadri40/koya-payment-reconciliation/main/expected.txt", "expected.txt")
# -------------------------------

total = 0.0
count = 0
latest_events = {}

# 1. Read the data and find the latest attempt for each transaction
with open("payments.jsonl") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        # Ignore lines that can't be read (dirty data)
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        # Ignore events without a txn_id
        txn_id = event.get("txn_id")
        if not txn_id:
            continue
        
        # Keep only the latest attempt based on timestamp
        ts = event.get("ts", "")
        if txn_id not in latest_events or ts > latest_events[txn_id].get("ts", ""):
            latest_events[txn_id] = event

# 2. Process the successful payments
for event in latest_events.values():
    if event.get("status") == "success":
        raw_amount = event.get("amount", 0)
        
        # Handle dirty data: amounts formatted as strings with commas
        if isinstance(raw_amount, str):
            raw_amount = raw_amount.replace(",", "")
            
        total += float(raw_amount)
        count += 1

# 3. Check against expected.txt
with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Code: KOYA-{round(total)}")