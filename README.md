# BACnet Server Example Python 2.7
A basic BACnet IP server example written with Python 2.7 using the [CAS BACnet Stack](https://www.bacnetstack.com/)

- Device: 389001 (Device Rainbow)
  - analog_input: 0 (AnalogInput Bronze)
  - analog_output: 1 (AnalogOutput Chartreuse)
  - analog_value: 2 (AnalogValue Diamond)
  - binary_input: 3 (BinaryInput Emerald)
  - binary_output: 4 (BinaryOutput Fuchsia)
  - binary_value: 5 (BinaryValue Gold)
  - multi_state_input: 13 (MultiStateInput Hot Pink)
  - multi_state_output: 14 (MultiStateOutput Indigo)
  - multi_state_value: 19 (MultiStateValue Kiwi)
  - characterstring_value: 40 (CharacterstringValue Nickel)
  - integer_value: 45 (IntegerValue Purple)
  - large_analog_value: 46 (LargeAnalogValue Quartz)
  - positive_integer_value: 48 (PositiveIntegerValue Silver)
  - NetworkPort: 56 (NetworkPort Umber)

## Example output

```txt
FYI: CAS BACnet Stack Python 2.7 Server Example v1.0.0
FYI: https://github.com/chipkin/BACnetServerExamplePython
('FYI: Libary path: ', WindowsPath('X:/Work/Repos/BACnetServerExamplePython2.7/CASBACnetStack_x86_Debug.dll'))
FYI: CAS BACnet Stack version: 3.31.3.0
FYI: CAS BACnet Stack python adapter version:0.0.4
FYI: Connecting UDP Resource to port=[47808]
('FYI: Local IP address: ', [192, 168, 1, 82])
FYI: Registering the Callback Functions with the CAS BACnet Stack
FYI: Setting up server Device. device.instance=[389001]
FYI: Adding AnalogInput. AnalogInput.instance=[0]
FYI: Adding BinaryInput. BinaryInput.instance=[3]
FYI: Adding MultiStateInput. MultiStateInput.instance=[13]
FYI: Adding analogOutput. analogOutput.instance=[1]
FYI: Adding analogValue. analogValue.instance=[2]
FYI: Adding binaryOutput. binaryOutput.instance=[4]
FYI: Adding binaryValue. binaryValue.instance=[5]
FYI: Adding multiStateOutput. multiStateOutput.instance=[14]
FYI: Adding multiStateOutput. multiStateValue.instance=[19]
FYI: Adding characterstringValue. characterstringValue.instance=[40]
FYI: Adding integerValue. integerValue.instance=[45]
FYI: Adding largeAnalogValue. largeAnalogValue.instance=[46]
FYI: Adding positiveIntegerValue. positiveIntegerValue.instance=[48]
FYI: Adding networkPort. networkPort.instance=[50]
FYI: Sending I-AM broadcast
('CallbackGetPropertyUInt', 389001L, 8, 389001L, 62L, False, 0L)
('CallbackGetPropertyUInt', 389001L, 8, 389001L, 120L, False, 0L)
('CallbackGetPropertyEnumerated', 389001L, 8, 389001L, 107L, 0L)
```

## Building

This python script requires the [CAS BACnet Stack](https://www.bacnetstack.com/) DLL that can be purchased from [Chipkin Automation Systems](https://store.chipkin.com).

Place the DLL in the root folder. Windows: CASBACnetStack_x64_Release.dll, Linux: libCASBACnetStack_x64_Release.so

```bash
pip install pathlib
pip install dnspython
pip install netifaces
```

## Running

```bash
python BACnetServerExample.py

```

## Useful links

- [Python ctypes](https://docs.python.org/3/library/ctypes.html)
- [Python Bindings Overview](https://realpython.com/python-bindings-overview/)
- [CAS BACnet Explorer](https://store.chipkin.com/products/tools/cas-bacnet-explorer) - A BACnet Client that can be used to discover and poll this example BACnet Server.
