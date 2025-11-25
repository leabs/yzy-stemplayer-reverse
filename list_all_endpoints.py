import usb.core
import usb.util

# Find the Teenage Engineering Stem Player
VENDOR_ID = 0x2367
PRODUCT_ID = 0x1701

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    raise ValueError("Stem Player not found")

print("Found device.")

# Set the active configuration (usually config 1)
try:
    dev.set_configuration()
except usb.core.USBError as e:
    print(f"Warning: could not set configuration: {e}")

print()

# Iterate through all configurations and dump interfaces/endpoints
for config in dev:
    print(f"Configuration {config.bConfigurationValue}")
    for intf in config:
        print(f"  Interface {intf.bInterfaceNumber}, AltSetting {intf.bAlternateSetting}, Class {intf.bInterfaceClass}")
        for ep in intf:
            direction = "IN" if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN else "OUT"
            print(f"    Endpoint {ep.bEndpointAddress:#04x} ({direction})")
            print(f"      Type: {usb.util.endpoint_type(ep.bmAttributes)}")
            print(f"      MaxPacketSize: {ep.wMaxPacketSize}")
            print(f"      Interval: {ep.bInterval}")

print("\nDone.")
