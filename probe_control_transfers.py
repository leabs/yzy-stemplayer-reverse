import usb.core
import usb.util
import usb.backend.libusb1
import usb.control

backend = usb.backend.libusb1.get_backend()
dev = usb.core.find(idVendor=0x2367, idProduct=0x1701, backend=backend)

if dev is None:
    raise ValueError("Stem Player not found")

print("Found device.")

dev.set_configuration()
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

if dev.is_kernel_driver_active(intf.bInterfaceNumber):
    dev.detach_kernel_driver(intf.bInterfaceNumber)

usb.util.claim_interface(dev, intf)



for request in range(1, 32):
    try:
        response = dev.ctrl_transfer(
            bmRequestType=usb.util.build_request_type(
                usb.util.CTRL_IN, usb.util.CTRL_TYPE_VENDOR, usb.util.CTRL_RECIPIENT_DEVICE
            ),
            bRequest=request,
            wValue=0,
            wIndex=0,
            data_or_wLength=64,
            timeout=200
        )
        print(f"Request 0x{request:02X}: Response {list(response)}")
    except usb.core.USBError as e:
        print(f"Request 0x{request:02X}: {e}")
