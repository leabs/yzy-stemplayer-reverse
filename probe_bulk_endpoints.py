import usb.core
import usb.util
import usb.backend.libusb1

backend = usb.backend.libusb1.get_backend()
dev = usb.core.find(idVendor=0x2367, idProduct=0x1701, backend=backend)

if dev is None:
    raise ValueError("Stem Player not found")

print("Found device.")

# Set configuration and claim interface
dev.set_configuration()
cfg = dev.get_active_configuration()

for intf in cfg:
    if dev.is_kernel_driver_active(intf.bInterfaceNumber):
        dev.detach_kernel_driver(intf.bInterfaceNumber)
    usb.util.claim_interface(dev, intf)

    print(f"Interface {intf.bInterfaceNumber} (Class {intf.bInterfaceClass})")
    for ep in intf:
        ep_type = usb.util.endpoint_type(ep.bmAttributes)
        ep_dir = "IN" if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN else "OUT"
        ep_type_str = {
            usb.util.ENDPOINT_TYPE_BULK: "BULK",
            usb.util.ENDPOINT_TYPE_INTERRUPT: "INTERRUPT",
            usb.util.ENDPOINT_TYPE_ISOCHRONOUS: "ISO",
            usb.util.ENDPOINT_TYPE_CONTROL: "CONTROL"
        }.get(ep_type, f"UNKNOWN ({ep_type})")

        print(f"  Endpoint 0x{ep.bEndpointAddress:02X} ({ep_dir}, {ep_type_str}), MaxPacketSize={ep.wMaxPacketSize}")
