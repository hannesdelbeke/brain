#!/usr/bin/env python3
"""
Tuiss SmartView / Hunter Douglas Motor Bluetooth LE Controller.
Controls blind position (0-100%), open, close, or stop via reverse-engineered GATT protocol.
"""

import argparse
import asyncio
import datetime
import os
import sys
from bleak import BleakClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Standard Tuiss SmartView GATT Characteristics
DEFAULT_WRITE_UUID = "00010405-0405-0607-0809-0a0b0c0d1910"
DEFAULT_NOTIFY_UUID = "00010304-0405-0607-0809-0a0b0c0d1910"

# Protocol Constants
CONNECTION_HANDSHAKE = bytes.fromhex("ff03030303787878787878")
CMD_INIT_QUERY = bytes.fromhex("ff78ea41d10301")
CMD_STOP = bytes.fromhex("ff78ea415f0301")
CMD_BATTERY_QUERY = bytes.fromhex("ff78ea41f00301")


def calculate_position_payload(user_percent: float) -> bytes:
    """
    Convert Home Assistant / standard position percentage (0 = Closed, 100 = Fully Open)
    to the Tuiss 8-byte inverted hex command.
    """
    tuiss_percent = max(0.0, min(100.0, 100.0 - user_percent))
    total_val = int(round(tuiss_percent * 10))  # Range 0 (Open) to 1000 (Closed)

    position_value = total_val % 256
    group_value = total_val // 256

    hex_str = f"ff78ea41bf03{position_value:02x}{group_value:02x}"
    return bytes.fromhex(hex_str)


def generate_timestamp_payload() -> bytes:
    """Generate dynamic real-time clock synchronization packet."""
    now = datetime.datetime.now()
    year = now.year - 2000
    ts_hex = f"ff78ea41{year:02x}{now.month:02x}{now.day:02x}{now.hour:02x}{now.minute:02x}{now.second:02x}"
    return bytes.fromhex(ts_hex)


def on_motor_feedback(sender, data: bytearray):
    print(f"[MOTOR FEEDBACK] {sender}: {data.hex()} (len {len(data)})")


async def execute_command(
    mac: str,
    action: str,
    position: float | None = None,
    timeout: float = 15.0,
):
    print("=" * 68)
    print("🪟 TUISS SMARTVIEW BLE CONTROLLER")
    print(f"Target Motor MAC: {mac}")
    print("=" * 68)

    # Determine command payload
    if action == "stop":
        cmd_payload = CMD_STOP
        desc = "EMERGENCY STOP"
    elif action == "open":
        cmd_payload = calculate_position_payload(100.0)
        desc = "MOVE FULLY OPEN (100%)"
    elif action == "close":
        cmd_payload = calculate_position_payload(0.0)
        desc = "MOVE FULLY CLOSED (0%)"
    elif action == "battery":
        cmd_payload = CMD_BATTERY_QUERY
        desc = "QUERY BATTERY STATUS"
    elif position is not None:
        cmd_payload = calculate_position_payload(position)
        desc = f"SET POSITION TO {position}% OPEN"
    else:
        print("❌ Error: Specify --action (open|close|stop|battery) or --position (0-100)")
        return

    print(f"Connecting to motor at {mac} (timeout {timeout}s)...")
    try:
        async with BleakClient(mac, timeout=timeout) as client:
            print(f"✅ Connected: {client.is_connected}")

            # Discover matching write characteristic
            write_uuid = None
            notify_uuid = None
            for service in client.services:
                for char in service.characteristics:
                    if "write" in char.properties and not write_uuid:
                        write_uuid = char.uuid
                    if (
                        "notify" in char.properties or "indicate" in char.properties
                    ) and not notify_uuid:
                        notify_uuid = char.uuid

            write_char = write_uuid or DEFAULT_WRITE_UUID
            notify_char = notify_uuid or DEFAULT_NOTIFY_UUID

            if notify_char:
                try:
                    await client.start_notify(notify_char, on_motor_feedback)
                except Exception:
                    pass

            # 1. Connection maintain handshake
            print("1. Sending Connection Handshake...")
            await client.write_gatt_char(write_char, CONNECTION_HANDSHAKE, response=True)
            await asyncio.sleep(0.2)

            # 2. Timestamp synchronization
            ts_payload = generate_timestamp_payload()
            print(f"2. Synchronizing Clock: {ts_payload.hex()}...")
            await client.write_gatt_char(write_char, ts_payload, response=True)
            await asyncio.sleep(0.2)

            # 3. Initialization query
            print("3. Sending Initialization Frame...")
            await client.write_gatt_char(write_char, CMD_INIT_QUERY, response=True)
            await asyncio.sleep(0.2)

            # 4. Transmit action command
            print(f"4. Transmitting Command: {cmd_payload.hex()} ({desc})...")
            await client.write_gatt_char(write_char, cmd_payload, response=True)

            print("\n🚀 Command transmitted! Waiting 4s for motor response...")
            await asyncio.sleep(4.0)
            print("✅ Complete. Disconnecting to release Bluetooth lock.")
    except Exception as e:
        print(f"❌ Error communicating with motor: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Control Tuiss SmartView / Hunter Douglas BLE motorized blinds."
    )
    parser.add_argument(
        "--mac",
        "-m",
        type=str,
        default=os.environ.get("TUISS_BLIND_MAC"),
        help="Target motor MAC address (or set TUISS_BLIND_MAC env var)",
    )
    parser.add_argument(
        "--action",
        "-a",
        choices=["open", "close", "stop", "battery"],
        help="Action to perform (open, close, stop, battery)",
    )
    parser.add_argument(
        "--position",
        "-p",
        type=float,
        help="Target position percentage (0 = Closed, 100 = Fully Open)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=15.0,
        help="BLE connection timeout in seconds (default: 15.0)",
    )

    args = parser.parse_args()

    if not args.mac:
        print("❌ Error: Device MAC address is required.")
        print("Example: python tuiss_blind_controller.py --mac AA:BB:CC:11:22:33 --action open")
        sys.exit(1)

    if not args.action and args.position is None:
        print("❌ Error: Specify either --action (open|close|stop) or --position (0-100)")
        sys.exit(1)

    target_action = args.action or "set_position"
    asyncio.run(
        execute_command(
            mac=args.mac,
            action=target_action,
            position=args.position,
            timeout=args.timeout,
        )
    )


if __name__ == "__main__":
    main()
