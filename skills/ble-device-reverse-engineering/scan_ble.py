#!/usr/bin/env python3
"""
Scan for nearby Bluetooth Low Energy (BLE) devices and display advertised names,
RSSI signal strength, manufacturer data, and service UUIDs.
"""

import argparse
import asyncio
import sys
from bleak import BleakScanner

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def scan(timeout: float = 6.0):
    print(f"Scanning for BLE devices for {timeout} seconds...\n")
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)

    if not devices:
        print("No BLE devices discovered.")
        return

    print(f"Found {len(devices)} BLE devices:\n")
    print(
        f"{'Address / MAC':<20} | {'RSSI':<6} | {'Name / LocalName':<28} | {'Services / Manufacturer'}"
    )
    print("-" * 88)

    for address, (device, adv) in devices.items():
        name = device.name or adv.local_name or "<Unnamed>"
        mfg = list(adv.manufacturer_data.keys()) if adv.manufacturer_data else []
        services = adv.service_uuids if adv.service_uuids else []
        extra = f"Mfg: {mfg}" if mfg else ""
        if services:
            extra += f" Svc: {services[:2]}"
        print(f"{address:<20} | {adv.rssi:<6} | {name:<28} | {extra}")


def main():
    parser = argparse.ArgumentParser(description="Scan for nearby Bluetooth LE devices.")
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=6.0,
        help="Scan timeout in seconds (default: 6.0)",
    )
    args = parser.parse_args()
    asyncio.run(scan(args.timeout))


if __name__ == "__main__":
    main()
