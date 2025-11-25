# save as dump_interface_descriptors.py
import usb.core
import usb.util

dev = usb.core.find(idVendor=0x2367, idProduct=0x1701)
if dev is None:
    raise ValueError("Stem Player not found")

print("Found device.\n")

dev.set_configuration()
for cfg in dev:
    print(f"Configuration {cfg.bConfigurationValue}")
    for intf in cfg:
        print(f"  Interface {intf.bInterfaceNumber}, Alt {intf.bAlternateSetting}")
        print(f"    Class: {intf.bInterfaceClass}")
        print(f"    Subclass: {intf.bInterfaceSubClass}")
        print(f"    Protocol: {intf.bInterfaceProtocol}")
