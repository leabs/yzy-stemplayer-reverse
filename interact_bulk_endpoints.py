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

bulk_out = None
bulk_in = None

for ep in intf:
    if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
        bulk_out = ep
    elif usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
        bulk_in = ep

if bulk_out:
    print(f"Found bulk OUT endpoint: 0x{bulk_out.bEndpointAddress:02X}")
    try:
        dev.write(bulk_out.bEndpointAddress, b'\x00' * 64)
        print("Wrote dummy data to bulk OUT.")
    except usb.core.USBError as e:
        print(f"Write failed: {e}")
else:
    print("No bulk OUT endpoint found.")

if bulk_in:
    print(f"Found bulk IN endpoint: 0x{bulk_in.bEndpointAddress:02X}")
    try:
        data = dev.read(bulk_in.bEndpointAddress, 64)
        print(f"Read from bulk IN: {data}")
    except usb.core.USBError as e:
        print(f"Read failed: {e}")
else:
    print("No bulk IN endpoint found.")
