import usb.core
import usb.util

# Find the device (Teenage Engineering Stem Player)
dev = usb.core.find(idVendor=0x2367, idProduct=0x1701)

if dev is None:
    raise ValueError("Stem Player not found")

print("Found device. Scanning for readable memory regions via control IN transfers...\n")

# Set configuration
dev.set_configuration()

# Attempt to read control IN transfers from various address ranges
for addr in range(0x0000, 0x10000, 0x1000):  # 64KB space, 4KB steps
    try:
        response = dev.ctrl_transfer(
            bmRequestType=usb.util.build_request_type(
                usb.util.CTRL_IN, usb.util.CTRL_TYPE_VENDOR, usb.util.CTRL_RECIPIENT_DEVICE
            ),
            bRequest=0x01,
            wValue=(addr & 0xFFFF),
            wIndex=(addr >> 16) & 0xFFFF,
            data_or_wLength=64,
            timeout=200
        )
        if response:
            print(f"Readable at 0x{addr:06X}: {response.hex()}")
        else:
            print(f"Readable at 0x{addr:06X}: No data")
    except usb.core.USBError as e:
        print(f"0x{addr:06X}: Read failed - {e}")

print("\nDone.")
