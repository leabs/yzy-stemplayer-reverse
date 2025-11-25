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

for i, intf in enumerate(cfg):
    print(f"\nInterface {intf.bInterfaceNumber}, AltSetting {intf.bAlternateSetting}, Class {intf.bInterfaceClass}")
    for ep in intf:
        ep_type = usb.util.endpoint_type(ep.bmAttributes)
        ep_dir = "IN" if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN else "OUT"
        print(f"  Endpoint Address: 0x{ep.bEndpointAddress:02X} ({ep_dir})")
        print(f"    Type: {ep_type}")
        print(f"    MaxPacketSize: {ep.wMaxPacketSize}")
        print(f"    Interval: {ep.bInterval}")
