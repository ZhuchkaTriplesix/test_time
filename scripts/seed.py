#!/usr/bin/env python3
"""Demo seeding script for SLA Response Time Control Service."""

import argparse
import json
import time
import urllib.error
import urllib.request


def send_event(base_url: str, event_data: dict) -> dict:
    url = f"{base_url.rstrip('/')}/api/events"
    req = urllib.request.Request(
        url,
        data=json.dumps(event_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"Error {e.code}: {body}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="Seed demo tickets and events into the service.")
    parser.add_argument(
        "--host",
        default="http://localhost:8000",
        help="Base URL of the Backend API (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    print(f"Connecting to {args.host}...")

    # 1. Send client message (General)
    evt1 = {
        "external_event_id": f"seed_client_01_{int(time.time())}",
        "event_type": "client",
        "external_client_id": "tg_user_ivan_45",
        "topic": "Техническая поддержка",
        "content": "Не могу авторизоваться в личном кабинете через мобильное приложение.",
    }
    r1 = send_event(args.host, evt1)
    print(f"Created ticket 1: {r1.get('ticket_id')} (Status: {r1.get('status')})")

    # 2. Send client message (Billing)
    evt2 = {
        "external_event_id": f"seed_client_02_{int(time.time())}",
        "event_type": "client",
        "external_client_id": "crm_client_elena_88",
        "topic": "Платежи и биллинг",
        "content": "Двойное списание средств по подписке Premium за август.",
    }
    r2 = send_event(args.host, evt2)
    print(f"Created ticket 2: {r2.get('ticket_id')} (Status: {r2.get('status')})")

    # 3. Send client message (General)
    evt3 = {
        "external_event_id": f"seed_client_03_{int(time.time())}",
        "event_type": "client",
        "external_client_id": "tg_alex_99",
        "topic": "Общие вопросы",
        "content": "Подскажите режим работы службы поддержки в выходные дни.",
    }
    r3 = send_event(args.host, evt3)
    ticket_3_id = r3.get("ticket_id")
    print(f"Created ticket 3: {ticket_3_id} (Status: {r3.get('status')})")

    # 4. Immediately answer ticket 3 (to demonstrate answered metric)
    if ticket_3_id:
        evt_ans = {
            "external_event_id": f"seed_agent_03_{int(time.time())}",
            "event_type": "agent",
            "ticket_id": ticket_3_id,
            "content": "Здравствуйте! Наша поддержка работает круглосуточно 24/7.",
        }
        r_ans = send_event(args.host, evt_ans)
        print(f"Answered ticket 3: {r_ans.get('ticket_id')} (Status: {r_ans.get('status')})")

    print("\nDemo seed completed successfully! Check the dashboard at http://localhost:3000")


if __name__ == "__main__":
    main()
