# try_enter_dfu_interface.py
import usb.core
import usb.util
import time

dev = usb.core.find(idVendor=0x2367, idProduct=0x1701)
if dev is None:
    raise ValueError("Stem Player not found")

print("Found device. Attempting vendor-specific OUT requests to interface...")

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
                usb.util.CTRL_RECIPIENT_INTERFACE
            ),
            bRequest=req,
            wValue=0,
            wIndex=intf.bInterfaceNumber,
            data_or_wLength=None,
            timeout=200
        )
        print(f"Sent OUT vendor request 0x{req:02X} to interface")
        time.sleep(0.25)
    except usb.core.USBError:
        continue
