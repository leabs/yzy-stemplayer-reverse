import usb.core
import usb.util
import usb.backend.libusb1

backend = usb.backend.libusb1.get_backend()

dev = usb.core.find(idVendor=0x2367, idProduct=0x1701, backend=backend)
if dev is None:
    raise ValueError("Stem Player not found")

print("Found device.\n")

dev.set_configuration()
cfg = dev.get_active_configuration()

# Each interface setting is a separate object in cfg
for intf in cfg:
    print(f"Interface {intf.bInterfaceNumber}, AltSetting {intf.bAlternateSetting}, Class {intf.bInterfaceClass}")

    try:
        usb.util.claim_interface(dev, intf)
    except usb.core.USBError as e:
        print(f"  Could not claim interface {intf.bInterfaceNumber}: {e}")
        continue

    for ep in intf.endpoints():
        print(f"  Endpoint 0x{ep.bEndpointAddress:02X}, Attributes 0x{ep.bmAttributes:02X}, MaxPacketSize {ep.wMaxPacketSize}")

print("\nDone.")
