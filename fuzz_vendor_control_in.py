import usb.core
import usb.util

# Replace with your Stem Player's vendor and product ID
VENDOR_ID = 0x2367
PRODUCT_ID = 0x1701

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    raise ValueError("Stem Player not found")

# Set configuration if needed
try:
    dev.set_configuration()
except usb.core.USBError as e:
    print(f"Could not set configuration: {e}")

print("Probing vendor-specific control IN requests...")

for request in range(0x00, 0x100):
    try:
        response = dev.ctrl_transfer(
            bmRequestType=usb.util.build_request_type(
                usb.util.CTRL_IN,
                usb.util.CTRL_TYPE_VENDOR,
                usb.util.CTRL_RECIPIENT_INTERFACE
            ),
            bRequest=request,
            wValue=0,
            wIndex=0,
            data_or_wLength=64,
            timeout=500
        )
        print(f"Request 0x{request:02X}: {response}")
    except usb.core.USBError as e:
        print(f"Request 0x{request:02X} failed: {e}")
