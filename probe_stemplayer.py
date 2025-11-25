import os
from pathlib import Path
import sys
import usb.core
import usb.util
import usb.backend.libusb1
import libusb_package
import time
import binascii


def find_libusb_dll() -> str | None:
    """Search sys.path for a libusb-1.0.dll we can point pyusb at."""
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


# Ask pyusb to use a libusb backend. Prefer the bundled DLL, fall back to any discovered DLL.
backend = libusb_package.get_libusb1_backend()
if backend is None:
    dll_path = find_libusb_dll()
    if dll_path:
        backend = usb.backend.libusb1.get_backend(find_library=lambda _: dll_path)

if backend is None:
    raise RuntimeError("No libusb backend found. Install drivers (WinUSB/libusbK via Zadig) and ensure a libusb-1.0.dll is accessible.")

# Find the device (Teenage Engineering Stem Player prototype)
dev = usb.core.find(idVendor=0x2367, idProduct=0x1701, backend=backend)

if dev is None:
    raise ValueError("Stem Player not found. Check driver & USB connection.")

# Set configuration
try:
    dev.set_configuration()
except Exception as e:
    print("Could not set configuration:", e)


def parse_hex_bytes(val: str) -> bytes:
    """Parse a hex string like '01 02 0a' or '01020a' into bytes."""
    val = val.strip().replace(" ", "").replace("0x", "")
    return binascii.unhexlify(val)


def hexdump(data: bytes, width: int = 16) -> None:
    """Simple hex/ascii dump."""
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        asc_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{i:04x}: {hex_part:<{width*3}} {asc_part}")


def dump_config_descriptor(dev, cfg_index: int = 0) -> None:
    """Fetch and dump raw config descriptor via control transfer."""
    try:
        hdr = dev.ctrl_transfer(0x80, 6, (2 << 8) | cfg_index, 0, 9)
        total_len = hdr[2] | (hdr[3] << 8)
        full = dev.ctrl_transfer(0x80, 6, (2 << 8) | cfg_index, 0, total_len)
        print(f"\n=== RAW CONFIG DESCRIPTOR ({total_len} bytes) ===")
        hexdump(bytes(full))
    except Exception as e:
        print("\nCould not read raw config descriptor:", e)

# Print descriptors and endpoints
print("\n=== DEVICE DESCRIPTOR ===")
print(f" USB: {dev.bcdUSB >> 8}.{dev.bcdUSB & 0xff:02x}")
print(f" VID:PID: {hex(dev.idVendor)}:{hex(dev.idProduct)}")
print(f" MaxPacket0: {dev.bMaxPacketSize0}")
print(f" Class/Sub/Prot: {hex(dev.bDeviceClass)}/{hex(dev.bDeviceSubClass)}/{hex(dev.bDeviceProtocol)}")

print("\n=== USB CONFIGURATION ===")
for cfg in dev:
    print(f"Configuration: {cfg.bConfigurationValue}, Attributes: {hex(cfg.bmAttributes)}, MaxPower: {cfg.bMaxPower * 2} mA")
    for intf in cfg:
        print(f" Interface: {intf.bInterfaceNumber}, Alt: {intf.bAlternateSetting}, Class/Sub/Prot: {hex(intf.bInterfaceClass)}/{hex(intf.bInterfaceSubClass)}/{hex(intf.bInterfaceProtocol)}")
        for ep in intf:
            direction = usb.util.endpoint_direction(ep.bEndpointAddress)
            ep_type = usb.util.endpoint_type(ep.bmAttributes)
            dir_str = "IN" if direction == usb.util.ENDPOINT_IN else "OUT"
            type_str = {usb.util.ENDPOINT_TYPE_CONTROL: "CTRL",
                        usb.util.ENDPOINT_TYPE_ISOCHRONOUS: "ISO",
                        usb.util.ENDPOINT_TYPE_BULK: "BULK",
                        usb.util.ENDPOINT_TYPE_INTERRUPT: "INTR"}.get(ep_type, f"0x{ep_type:x}")
            print(f"  Endpoint: {hex(ep.bEndpointAddress)} ({dir_str}), Type: {type_str}, MaxPacket: {ep.wMaxPacketSize}, Interval: {ep.bInterval}")

try:
    print("\n=== STRINGS ===")
    print(" Manufacturer:", usb.util.get_string(dev, dev.iManufacturer))
    print(" Product     :", usb.util.get_string(dev, dev.iProduct))
    print(" Serial      :", usb.util.get_string(dev, dev.iSerialNumber))
except Exception as e:
    print("Could not read string descriptors:", e)

# Optional raw config descriptor dump: PROBE_RAW=1
if os.environ.get("PROBE_RAW") == "1":
    dump_config_descriptor(dev, cfg_index=0)

# Optional poke: set PROBE_RW=1 to try simple reads/writes on discovered endpoints.
if os.environ.get("PROBE_RW") == "1":
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]
    try:
        usb.util.claim_interface(dev, intf.bInterfaceNumber)
    except Exception:
        pass
    print("\n=== PROBE RW (non-destructive) ===")
    for ep in intf:
        direction = usb.util.endpoint_direction(ep.bEndpointAddress)
        try:
            if direction == usb.util.ENDPOINT_IN:
                size = min(64, ep.wMaxPacketSize or 64)
                data = dev.read(ep.bEndpointAddress, size, intf.bInterfaceNumber, timeout=200)
                print(f" Read from {hex(ep.bEndpointAddress)}: {bytes(data).hex()}")
            else:
                size = min(8, ep.wMaxPacketSize or 8)
                payload = bytes([0x00] * size)
                wrote = dev.write(ep.bEndpointAddress, payload, intf.bInterfaceNumber, timeout=200)
                print(f" Wrote {wrote} zero bytes to {hex(ep.bEndpointAddress)}")
        except Exception as e:
            print(f" Endpoint {hex(ep.bEndpointAddress)} error: {e}")

# Optional continuous read from first BULK/INTR IN endpoint: PROBE_STREAM=1
if os.environ.get("PROBE_STREAM") == "1":
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]
    in_eps = [ep for ep in intf if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN and usb.util.endpoint_type(ep.bmAttributes) in (usb.util.ENDPOINT_TYPE_BULK, usb.util.ENDPOINT_TYPE_INTERRUPT)]
    if not in_eps:
        print("\n=== PROBE STREAM ===")
        print(" No BULK/INTR IN endpoints found.")
    else:
        ep = in_eps[0]
        try:
            usb.util.claim_interface(dev, intf.bInterfaceNumber)
        except Exception:
            pass
        print(f"\n=== PROBE STREAM on {hex(ep.bEndpointAddress)} ({'INTR' if usb.util.endpoint_type(ep.bmAttributes)==usb.util.ENDPOINT_TYPE_INTERRUPT else 'BULK'}) ===")
        for i in range(20):
            try:
                size = min(256, ep.wMaxPacketSize or 256)
                data = dev.read(ep.bEndpointAddress, size, intf.bInterfaceNumber, timeout=200)
                print(f" [{i:02d}] {bytes(data).hex()}")
            except Exception as e:
                print(f" [{i:02d}] error: {e}")
            time.sleep(0.05)

# Manual control transfer helper (for replaying captured requests): set CTRL_SEND=1 and env vars.
if os.environ.get("CTRL_SEND") == "1":
    bmRequestType = int(os.environ.get("CTRL_BMREQ", "0xc0"), 16)
    bRequest = int(os.environ.get("CTRL_BREQ", "0"), 16)
    wValue = int(os.environ.get("CTRL_WVALUE", "0"), 16)
    wIndex = int(os.environ.get("CTRL_WINDEX", "0"), 16)
    length = int(os.environ.get("CTRL_LEN", "0"), 0)
    payload = os.environ.get("CTRL_DATA")
    timeout = int(os.environ.get("CTRL_TIMEOUT", "500"), 10)
    repeat = int(os.environ.get("CTRL_REPEAT", "1"), 10)

    print(f"\n=== CTRL TRANSFER ({repeat}x) ===")
    print(f" bmRequestType={hex(bmRequestType)} bRequest={hex(bRequest)} wValue={hex(wValue)} wIndex={hex(wIndex)} length={length} timeout={timeout}")
    if payload:
        try:
            out_data = parse_hex_bytes(payload)
        except Exception as e:
            raise SystemExit(f"Failed to parse CTRL_DATA: {e}")
        print(f" payload ({len(out_data)} bytes): {out_data.hex()}")
    else:
        out_data = None

    for i in range(repeat):
        try:
            if bmRequestType & 0x80:
                data = dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, length, timeout=timeout)
                print(f" [{i}] IN -> {bytes(data).hex()}")
            else:
                sent = dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, out_data or [], timeout=timeout)
                print(f" [{i}] OUT sent={sent}")
        except Exception as e:
            print(f" [{i}] error: {e}")
