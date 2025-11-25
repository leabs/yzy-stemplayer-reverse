import usb.core
import usb.util
import time

# Locate the Stem Player
dev = usb.core.find(idVendor=0x2367, idProduct=0x1701)
if dev is None:
    raise ValueError("Stem Player not found")

# Set configuration and interface
dev.set_configuration()
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]
usb.util.claim_interface(dev, intf.bInterfaceNumber)

print("Found device. Sending OUT requests followed by GETSTATUS...")

for request in range(256):
    try:
        dev.ctrl_transfer(
            bmRequestType=usb.util.build_request_type(
                usb.util.CTRL_OUT, usb.util.CTRL_TYPE_VENDOR, usb.util.CTRL_RECIPIENT_INTERFACE
            ),
            bRequest=request,
            wValue=0,
            wIndex=0,
            data_or_wLength=[]
        )
        time.sleep(0.05)

        response = dev.ctrl_transfer(
            bmRequestType=usb.util.build_request_type(
                usb.util.CTRL_IN, usb.util.CTRL_TYPE_CLASS, usb.util.CTRL_RECIPIENT_INTERFACE
            ),
            bRequest=0x03,  # DFU_GETSTATUS
            wValue=0,
            wIndex=0,
            data_or_wLength=6
        )
        print(f"Request 0x{request:02X} → GETSTATUS: {response}")
    except usb.core.USBError as e:
        print(f"Request 0x{request:02X} failed: {e}")

print("Done.")
