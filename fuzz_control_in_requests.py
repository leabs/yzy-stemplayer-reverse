import usb.core
import usb.util

# Find the device by vendor and product ID
dev = usb.core.find(idVendor=0x2367, idProduct=0x1701)

if dev is None:
    raise ValueError("Stem Player not found")

dev.set_configuration()

print("Found device. Probing all control IN requests at addr 0x000000...")

for bRequest in range(0x00, 0x100):
    try:
        response = dev.ctrl_transfer(
            bmRequestType=usb.util.build_request_type(
                usb.util.CTRL_IN,
                usb.util.CTRL_TYPE_VENDOR,
                usb.util.CTRL_RECIPIENT_DEVICE,
            ),
            bRequest=bRequest,
            wValue=0x0000,
            wIndex=0,
            data_or_wLength=64,
            timeout=500,
        )
        print(f"Request 0x{bRequest:02X} succeeded: {response}")
    except usb.core.USBError as e:
        print(f"Request 0x{bRequest:02X} failed: {str(e)}")

print("Done.")
