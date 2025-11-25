import usb.core
import usb.util

# Find the device
VENDOR_ID = 0x2367
PRODUCT_ID = 0x1701
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    raise ValueError("Stem Player not found")

print("Found device.")

# Set configuration
try:
    dev.set_configuration()
except usb.core.USBError:
    pass  # May already be set

bmRequestType = usb.util.build_request_type(
    usb.util.CTRL_OUT,
    usb.util.CTRL_TYPE_VENDOR,
    usb.util.CTRL_RECIPIENT_INTERFACE
)

# Loop over potential wIndex and wValue combinations
for wIndex in range(0, 4):  # Try 0-3 interfaces
    for wValue in range(0x00, 0x100):  # Try a range of values
        for bRequest in range(0x00, 0x100):
            try:
                dev.ctrl_transfer(
                    bmRequestType,
                    bRequest=bRequest,
                    wValue=wValue,
                    wIndex=wIndex,
                    data_or_wLength=[]
                )
                print(f"Request 0x{bRequest:02X} succeeded (wValue=0x{wValue:02X}, wIndex=0x{wIndex:02X})")
            except usb.core.USBError as e:
                if e.errno != 32:
                    print(f"Request 0x{bRequest:02X} error: {e} (wValue=0x{wValue:02X}, wIndex=0x{wIndex:02X})")

print("Done.")