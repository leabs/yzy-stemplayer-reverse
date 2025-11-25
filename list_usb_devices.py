import usb.core
import usb.util
import usb.backend.libusb1

# Force PyUSB to use the Homebrew-installed libusb
backend = usb.backend.libusb1.get_backend(
    find_library=lambda x: "/opt/homebrew/lib/libusb-1.0.dylib"
)

if backend is None:
    raise ValueError("libusb backend not found or failed to load.")

# List all connected USB devices
devices = usb.core.find(find_all=True, backend=backend)

if devices is None:
    print("No USB devices found.")
else:
    for dev in devices:
        print(f"Device: ID {hex(dev.idVendor)}:{hex(dev.idProduct)}")
        try:
            print(f"  Manufacturer: {usb.util.get_string(dev, dev.iManufacturer)}")
            print(f"  Product: {usb.util.get_string(dev, dev.iProduct)}")
            print(f"  Serial Number: {usb.util.get_string(dev, dev.iSerialNumber)}")
        except usb.core.USBError as e:
            print(f"  Error retrieving strings: {e}")
