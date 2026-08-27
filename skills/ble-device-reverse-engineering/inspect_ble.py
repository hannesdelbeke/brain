#!/usr/bin/env python3
"""
Inspect GATT Services, Characteristics, and Descriptors of a target BLE device.
"""

import argparse
import asyncio
import sys
from bleak import BleakClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def inspect_device(target_mac: str, timeout: float = 12.0):
    print(f"Connecting to BLE device: {target_mac} (timeout: {timeout}s)...")
    try:
        async with BleakClient(target_mac, timeout=timeout) as client:
            print(f"✅ Connected: {client.is_connected}")
            print("\n" + "=" * 70)
            print("GATT SERVICES & CHARACTERISTICS")
            print("=" * 70)

            for service in client.services:
                print(f"\n[Service] {service.uuid} ({service.description})")
                for char in service.characteristics:
                    props = ", ".join(char.properties)
                    print(
                        f"  └── [Char] {char.uuid} | Props: [{props}] ({char.description})"
                    )
                    if "read" in char.properties:
                        try:
                            val = await client.read_gatt_char(char.uuid)
                            ascii_val = "".join(
                                [chr(b) if 32 <= b <= 126 else "." for b in val]
                            )
                            print(
                                f"       Hex: {val.hex()} | ASCII: {ascii_val}"
                            )
                        except Exception as e:
                            print(f"       Read error: {e}")

            print("\n" + "=" * 70)
            print("Inspection complete. Connection closed.")
    except Exception as e:
        print(f"❌ Failed to connect or inspect: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect GATT Services and Characteristics of a BLE device."
    )
    parser.add_argument(
        "mac",
        type=str,
        help="Target BLE MAC address (e.g. AA:BB:CC:DD:EE:FF)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=12.0,
        help="Connection timeout in seconds (default: 12.0)",
    )
    args = parser.parse_args()
    asyncio.run(inspect_device(args.mac, args.timeout))


if __name__ == "__main__":
    main()
