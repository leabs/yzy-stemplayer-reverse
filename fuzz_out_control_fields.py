import usb.core
import usb.util
import usb.backend.libusb1
import usb.control

VENDOR_ID = 0x2367
PRODUCT_ID = 0x1701

backend = usb.backend.libusb1.get_backend()
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, backend=backend)

if dev is None:
    raise ValueError("Stem Player not found")

print("Found device.")

dev.set_configuration()
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

if dev.is_kernel_driver_active(intf.bInterfaceNumber):
    dev.detach_kernel_driver(intf.bInterfaceNumber)

usb.util.claim_interface(dev, intf)

# Try bRequest = 0x01 with different wValue and wIndex
for wValue in range(0x00, 0x10):
    for wIndex in range(0x00, 0x10):
        try:
            result = dev.ctrl_transfer(
                bmRequestType=usb.util.build_request_type(
                    usb.util.CTRL_OUT, usb.util.CTRL_TYPE_VENDOR, usb.util.CTRL_RECIPIENT_DEVICE
                ),
                bRequest=0x01,
                wValue=wValue,
                wIndex=wIndex,
                data_or_wLength=[0x00, 0x01, 0x02, 0x03],  # dummy payload
                timeout=200
            )
            print(f"Success: wValue=0x{wValue:02X}, wIndex=0x{wIndex:02X}, result={result}")
        except usb.core.USBError as e:
            print(f"Fail:    wValue=0x{wValue:02X}, wIndex=0x{wIndex:02X} -> {e}")
