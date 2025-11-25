import usb.core
import usb.util
import usb.backend.libusb1
import usb.control

# Device identifiers
VENDOR_ID = 0x2367
PRODUCT_ID = 0x1701

# Load libusb backend explicitly
backend = usb.backend.libusb1.get_backend()
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, backend=backend)

if dev is None:
    raise ValueError("Stem Player not found")

print("Found device.")

# Set configuration and claim interface
dev.set_configuration()
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

if dev.is_kernel_driver_active(intf.bInterfaceNumber):
    dev.detach_kernel_driver(intf.bInterfaceNumber)

usb.util.claim_interface(dev, intf)

# Try sending OUT control transfer with dummy payload
try:
    result = dev.ctrl_transfer(
        bmRequestType=usb.util.build_request_type(
            usb.util.CTRL_OUT, usb.util.CTRL_TYPE_VENDOR, usb.util.CTRL_RECIPIENT_DEVICE
        ),
        bRequest=0x01,              # arbitrary request code
        wValue=0x0000,
        wIndex=0x0000,
        data_or_wLength=[0x01, 0x02, 0x03, 0x04],  # 4-byte dummy payload
        timeout=200
    )
    print("OUT transfer succeeded:", result)
except usb.core.USBError as e:
    print("OUT transfer failed:", e)
