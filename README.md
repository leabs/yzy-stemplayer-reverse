# Stem Player USB fuzzing scripts

Quick scripts for probing the Teenage Engineering Stem Player (VID 0x2367, PID 0x1701) over USB with PyUSB.

## Dependencies
- Python 3
- `pyusb` with a libusb backend installed (`libusb-1.0` on most platforms)
- Permission to talk to the device (udev rules on Linux or run with `sudo`)

Install Python deps: `python3 -m pip install pyusb`

## Script rundown
- `fuzz_control_in_requests.py`: Enumerates all vendor control IN `bRequest` values at `wValue=0`, `wIndex=0`, reading 64 bytes to see which requests respond. Run: `python fuzz_control_in_requests.py`
- `fuzz_control_out_requests.py`: Sends vendor control OUT requests across all `bRequest` values, `wValue` 0x00-0xFF, and interface indices 0-3 to see which combinations are accepted. Run (macOS + Homebrew libusb): `DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 fuzz_control_out_requests.py`
- `probe_memory_read.py`: Tries vendor control IN `bRequest=0x01` reads over address space chunks (0x0000-0xFFFF in 4KB steps) to spot readable regions. Run: `python probe_memory_read.py`
- `try_enter_dfu.py`: Fires vendor control OUT requests (`bRequest` 0x00-0xFE) to the device recipient to look for a DFU entry trigger. Run: `python try_enter_dfu.py`
- `try_enter_dfu_interface.py`: Similar DFU attempt but targets the active interface recipient with vendor control OUT requests. Run: `python try_enter_dfu_interface.py`
