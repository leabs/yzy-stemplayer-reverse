import usb.core
import usb.util
import usb.backend.libusb1

backend = usb.backend.libusb1.get_backend()
dev = usb.core.find(idVendor=0x2367, idProduct=0x1701, backend=backend)

if dev is None:
    raise ValueError("Stem Player not found")
print("Found device.")

dev.set_configuration()
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

usb.util.claim_interface(dev, intf)

print("Probing variations of vendor-specific control IN transfers...")

for request in range(0x00, 0xFF + 1):
    for wValue in [0x0000, 0x0001, 0x0100, 0xFFFF]:
        for wIndex in [0x0000, intf.bInterfaceNumber]:
            for length in [4, 8, 16, 32, 64]:
                try:
                    response = dev.ctrl_transfer(
                        bmRequestType=usb.util.build_request_type(
                            usb.util.CTRL_IN,
                            usb.util.CTRL_TYPE_VENDOR,
                            usb.util.CTRL_RECIPIENT_INTERFACE
                        ),
                        bRequest=request,
                        wValue=wValue,
                        wIndex=wIndex,
                        data_or_wLength=length,
                        timeout=200
                    )
                    if response:
                        print(f"bRequest=0x{request:02X}, wValue=0x{wValue:04X}, wIndex=0x{wIndex:04X}, len={length} → Response: {response}")
                except usb.core.USBError:
                    continue
