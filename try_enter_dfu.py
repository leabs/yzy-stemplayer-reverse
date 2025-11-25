import usb.core
import usb.util
import time

dev = usb.core.find(idVendor=0x2367, idProduct=0x1701)
if dev is None:
    raise ValueError("Stem Player not found")

print("Found device. Attempting vendor-specific OUT requests...")

dev.set_configuration()
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]
usb.util.claim_interface(dev, intf)

for req in range(0x00, 0xFF):
    try:
        dev.ctrl_transfer(
            usb.util.build_request_type(
                usb.util.CTRL_OUT,
                usb.util.CTRL_TYPE_VENDOR,
                usb.util.CTRL_RECIPIENT_DEVICE
            ),
            bRequest=req,
            wValue=0,
            wIndex=0,
            data_or_wLength=None,
            timeout=200
        )
        print(f"Sent OUT vendor request 0x{req:02X}")
        time.sleep(0.5)
    except usb.core.USBError:
        continue
