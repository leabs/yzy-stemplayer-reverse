import usb.core
import usb.util

VENDOR_ID = 0x2367
PRODUCT_ID = 0x1701

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if dev is None:
    raise ValueError("Stem Player not found")

dev.set_configuration()

cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

usb.util.claim_interface(dev, intf)

response = dev.ctrl_transfer(
    bmRequestType=usb.util.build_request_type(
        usb.util.CTRL_IN, usb.util.CTRL_TYPE_CLASS, usb.util.CTRL_RECIPIENT_INTERFACE
    ),
    bRequest=0x03,  # DFU_GETSTATUS
    wValue=0,
    wIndex=intf.bInterfaceNumber,
    data_or_wLength=6,
    timeout=1000
)
print("DFU_GETSTATUS response:", response)
