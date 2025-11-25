import argparse
import binascii
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import usb.core
import usb.util
import usb.backend.libusb1
import libusb_package

LOG_FH = None


def log(msg: str = "") -> None:
    print(msg)
    if LOG_FH:
        LOG_FH.write(msg + "\n")
        LOG_FH.flush()


def find_libusb_dll() -> str | None:
    """Search sys.path for a libusb-1.0.dll."""
    for entry in sys.path:
        try:
            base = Path(entry)
        except TypeError:
            continue
        if not base.is_dir():
            continue
        for dll in base.rglob("libusb-1.0.dll"):
            return str(dll)
    return None


def get_backend():
    backend = libusb_package.get_libusb1_backend()
    if backend is None:
        dll_path = find_libusb_dll()
        if dll_path:
            backend = usb.backend.libusb1.get_backend(find_library=lambda _: dll_path)
    if backend is None:
        raise RuntimeError("No libusb backend found. Install drivers (WinUSB/libusbK via Zadig) and ensure a libusb-1.0.dll is accessible.")
    return backend


def parse_hex_bytes(val: str | None) -> bytes | None:
    if not val:
        return None
    cleaned = val.strip().replace(" ", "").replace("0x", "")
    if cleaned == "":
        return b""
    return binascii.unhexlify(cleaned)


def hexdump(data: bytes, width: int = 16) -> None:
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        asc_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        log(f"{i:04x}: {hex_part:<{width*3}} {asc_part}")


def dump_config_descriptor(dev, cfg_index: int = 0) -> None:
    try:
        hdr = dev.ctrl_transfer(0x80, 6, (2 << 8) | cfg_index, 0, 9)
        total_len = hdr[2] | (hdr[3] << 8)
        full = dev.ctrl_transfer(0x80, 6, (2 << 8) | cfg_index, 0, total_len)
        log(f"\n=== RAW CONFIG DESCRIPTOR ({total_len} bytes) ===")
        hexdump(bytes(full))
    except Exception as e:
        log("\nCould not read raw config descriptor:")
        log(str(e))


def print_info(dev):
    log("\n=== DEVICE DESCRIPTOR ===")
    log(f" USB: {dev.bcdUSB >> 8}.{dev.bcdUSB & 0xff:02x}")
    log(f" VID:PID: {hex(dev.idVendor)}:{hex(dev.idProduct)}")
    log(f" MaxPacket0: {dev.bMaxPacketSize0}")
    log(f" Class/Sub/Prot: {hex(dev.bDeviceClass)}/{hex(dev.bDeviceSubClass)}/{hex(dev.bDeviceProtocol)}")

    log("\n=== USB CONFIGURATION ===")
    for cfg in dev:
        log(f"Configuration: {cfg.bConfigurationValue}, Attributes: {hex(cfg.bmAttributes)}, MaxPower: {cfg.bMaxPower * 2} mA")
        for intf in cfg:
            log(f" Interface: {intf.bInterfaceNumber}, Alt: {intf.bAlternateSetting}, Class/Sub/Prot: {hex(intf.bInterfaceClass)}/{hex(intf.bInterfaceSubClass)}/{hex(intf.bInterfaceProtocol)}")
            for ep in intf:
                direction = usb.util.endpoint_direction(ep.bEndpointAddress)
                ep_type = usb.util.endpoint_type(ep.bmAttributes)
                dir_str = "IN" if direction == usb.util.ENDPOINT_IN else "OUT"
                type_str = {usb.util.ENDPOINT_TYPE_CONTROL: "CTRL",
                            usb.util.ENDPOINT_TYPE_ISOCHRONOUS: "ISO",
                            usb.util.ENDPOINT_TYPE_BULK: "BULK",
                            usb.util.ENDPOINT_TYPE_INTERRUPT: "INTR"}.get(ep_type, f"0x{ep_type:x}")
                log(f"  Endpoint: {hex(ep.bEndpointAddress)} ({dir_str}), Type: {type_str}, MaxPacket: {ep.wMaxPacketSize}, Interval: {ep.bInterval}")

    try:
        log("\n=== STRINGS ===")
        log(" Manufacturer: " + str(usb.util.get_string(dev, dev.iManufacturer)))
        log(" Product     : " + str(usb.util.get_string(dev, dev.iProduct)))
        log(" Serial      : " + str(usb.util.get_string(dev, dev.iSerialNumber)))
    except Exception as e:
        log("Could not read string descriptors: " + str(e))


def send_control(dev, args):
    log(f"\n=== CTRL TRANSFER ({args.repeat}x) ===")
    log(f" bmRequestType={hex(args.bmreq)} bRequest={hex(args.breq)} wValue={hex(args.wvalue)} wIndex={hex(args.windex)} length={args.length} timeout={args.timeout}")
    out_data = parse_hex_bytes(args.data)
    if out_data is not None and not (args.bmreq & 0x80):
        log(f" payload ({len(out_data)} bytes): {out_data.hex()}")
    for i in range(args.repeat):
        try:
            if args.bmreq & 0x80:
                data = dev.ctrl_transfer(args.bmreq, args.breq, args.wvalue, args.windex, args.length, timeout=args.timeout)
                log(f" [{i}] IN -> {bytes(data).hex()}")
            else:
                sent = dev.ctrl_transfer(args.bmreq, args.breq, args.wvalue, args.windex, out_data or [], timeout=args.timeout)
                log(f" [{i}] OUT sent={sent}")
        except Exception as e:
            log(f" [{i}] error: {e}")


def poll_control(dev, args):
    if not (args.bmreq & 0x80):
        log("\nPoll requires an IN control request; bmRequestType must have bit7 set.")
        return
    log(f"\n=== CTRL POLL ({'infinite' if args.poll_count == 0 else args.poll_count} iterations) ===")
    count = 0
    while args.poll_count == 0 or count < args.poll_count:
        try:
            data = dev.ctrl_transfer(args.bmreq, args.breq, args.wvalue, args.windex, args.length, timeout=args.timeout)
            log(f" [{count}] IN -> {bytes(data).hex()}")
        except Exception as e:
            log(f" [{count}] error: {e}")
        count += 1
        time.sleep(args.poll_interval)


def load_batch(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    try:
        items = json.loads(content)
    except Exception as e:
        raise SystemExit(f"Failed to parse batch file: {e}")
    if not isinstance(items, list):
        raise SystemExit("Batch file must be a JSON list of request objects.")
    return items


def snapshot_devices(backend):
    devs = []
    try:
        for d in usb.core.find(find_all=True, backend=backend):
            devs.append((d.idVendor, d.idProduct, getattr(d, "address", None)))
    except Exception:
        pass
    return set(devs)


def scan_after(backend, delay_sec: float):
    time.sleep(delay_sec)
    new_set = snapshot_devices(backend)
    log(f"\n=== SCAN AFTER {delay_sec:.2f}s ===")
    if not new_set:
        log(" Could not enumerate devices (permission/backend issue).")
    else:
        for vid, pid, addr in sorted(new_set):
            addr_part = f" addr={addr}" if addr is not None else ""
            log(f" Device: {hex(vid)}:{hex(pid)}{addr_part}")
    return new_set


def main():
    parser = argparse.ArgumentParser(description="Stem Player USB probe/control helper.")
    parser.add_argument("--bmreq", type=lambda x: int(x, 0), default=0xC0, help="bmRequestType (default 0xC0)")
    parser.add_argument("--breq", type=lambda x: int(x, 0), default=0x00, help="bRequest (default 0)")
    parser.add_argument("--wvalue", type=lambda x: int(x, 0), default=0x0000, help="wValue (default 0)")
    parser.add_argument("--windex", type=lambda x: int(x, 0), default=0x0000, help="wIndex (default 0)")
    parser.add_argument("--length", type=int, default=0, help="IN transfer length (bytes)")
    parser.add_argument("--data", type=str, default=None, help="OUT data payload as hex bytes (e.g. '01 02 0a')")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat count (default 1)")
    parser.add_argument("--timeout", type=int, default=500, help="Timeout ms (default 500)")
    parser.add_argument("--raw", action="store_true", help="Dump raw config descriptor")
    parser.add_argument("--no-info", action="store_true", help="Skip descriptor/info printout")
    parser.add_argument("--poll", action="store_true", help="Continuously poll IN control request")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="Seconds between polls (default 0.5)")
    parser.add_argument("--poll-count", type=int, default=0, help="Number of polls (0 = infinite)")
    parser.add_argument("--batch", type=str, help="JSON file with list of control requests to replay")
    parser.add_argument("--scan-after", type=float, default=0.0, help="After requests, wait N seconds then list devices")
    parser.add_argument("--logfile", type=str, help="Write output to a log file as well as stdout")
    args = parser.parse_args()

    global LOG_FH
    if args.logfile:
        LOG_FH = open(args.logfile, "a", encoding="utf-8")

    backend = get_backend()
    baseline_devices = snapshot_devices(backend)
    dev = usb.core.find(idVendor=0x2367, idProduct=0x1701, backend=backend)
    if dev is None:
        raise SystemExit("Stem Player not found. Check driver & USB connection.")
    try:
        dev.set_configuration()
    except Exception as e:
        log("Could not set configuration: " + str(e))

    if not args.no_info:
        print_info(dev)
    if args.raw:
        dump_config_descriptor(dev, cfg_index=0)

    if args.batch:
        items = load_batch(args.batch)
        log(f"\n=== BATCH ({len(items)} requests from {args.batch}) ===")
        for idx, item in enumerate(items):
            ns = SimpleNamespace(
                bmreq=int(item.get("bmreq", args.bmreq), 0) if isinstance(item.get("bmreq", args.bmreq), str) else int(item.get("bmreq", args.bmreq)),
                breq=int(item.get("breq", args.breq), 0) if isinstance(item.get("breq", args.breq), str) else int(item.get("breq", args.breq)),
                wvalue=int(item.get("wvalue", args.wvalue), 0) if isinstance(item.get("wvalue", args.wvalue), str) else int(item.get("wvalue", args.wvalue)),
                windex=int(item.get("windex", args.windex), 0) if isinstance(item.get("windex", args.windex), str) else int(item.get("windex", args.windex)),
                length=int(item.get("length", args.length)),
                data=item.get("data"),
                repeat=int(item.get("repeat", args.repeat)),
                timeout=int(item.get("timeout", args.timeout)),
            )
            log(f"\n--- Batch item {idx} ---")
            send_control(dev, ns)

    if args.breq or args.length or args.data is not None:
        send_control(dev, args)
    if args.poll:
        poll_control(dev, args)

    if args.scan_after > 0:
        new_set = scan_after(backend, args.scan_after)
        added = new_set - baseline_devices
        if added:
            log(" New devices detected since start:")
            for vid, pid, addr in sorted(added):
                addr_part = f" addr={addr}" if addr is not None else ""
                log(f"  {hex(vid)}:{hex(pid)}{addr_part}")
        else:
            log(" No new devices detected.")

    if not (args.breq or args.length or args.data is not None or args.batch or args.poll):
        log("\nNo control transfer requested. Use --breq/--length/--data or --batch to send one.")


if __name__ == "__main__":
    main()
