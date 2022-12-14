# CAS BACnet Stack Python Server Example 
# https://github.com/chipkin/BACnetServerExamplePython 
#
import ctypes
import io

import pathlib
import netifaces
import dns.resolver  # Package name: dnspython
import socket
import time  # Sleep function
from CASBACnetStackAdapter import *  # Contains all the Enumerations, and callback prototypes

bacnet_server_example_python27_version = "1.0.0"

# Example database
# -----------------------------------------------------------------------------
# This is an example database. Normally this data would come from your sensor/database
#
# Units.
# no_units (95),celsius (62)
# ...
#
# Reliability
# no-fault-detected (0),or (1)
# ...
db = {
    "device": {
        "instance": 389001,
        "objectName": "Device Rainbow",
        "vendorname": "Example Chipkin Automation Systems",
        "vendoridentifier": 0},
    "analogInput": {
        "instance": 0,
        "objectName": "AnalogInput Bronze",
        "presentValue": 99.6,
        "units": 62,
        "reliability": 1,
        "covIncrement": 1.0},
    "binaryInput": {
        "instance": 3,
        "objectName": "BinaryInput Emerald",
        "presentValue": 1,
        "reliability": 1,
        "activeText": "InAlarm",
        "inactiveText": "Normal"},
    "multiStateInput": {
        "instance": 13,
        "objectName": "MultiStateInput Hot Pink",
        "presentValue": 3,
        "numberOfStates": 3,
        "stateText": ["Off", "On", "Blinking"]},
    "analogOutput": {
        "instance": 1,
        "objectName": "AnalogOutput Chartreuse",
        "presentValue": 1},
    "analogValue": {
        "instance": 2,
        "objectName": "AnalogValue Diamond",
        "presentValue": 1,
        "covIncrement": 1.0},
    "binaryOutput": {
        "instance": 4,
        "objectName": "BinaryOutput Fuchsia",
        "presentValue": 1},
    "binaryValue": {
        "instance": 5,
        "objectName": "BinaryValue Gold",
        "presentValue": 1,
        "activeText": "On",
        "inactiveText": "Off"},
    "multiStateOutput": {
        "instance": 14,
        "objectName": "MultiStateOutput Indigo",
        "presentValue": 1,
        "numberOfStates": 4,
        "stateText": ["Off", "On", "Restart", "Error"]},
    "multiStateValue": {
        "instance": 19,
        "objectName": "MultiStateValue Kiwi",
        "presentValue": 1,
        "numberOfStates": 3,
        "stateText": ["Off", "On", "Blinking"]},
    "characterstringValue": {
        "instance": 40,
        "objectName": "CharacterstringValue Nickel",
        "presentValue": "Hello World"},
    "integerValue": {
        "instance": 45,
        "objectName": "IntegerValue Purple",
        "presentValue": 1},
    "largeAnalogValue": {
        "instance": 46,
        "objectName": "LargeAnalogValue Quartz",
        "presentValue": 1},
    "positiveIntegerValue": {
        "instance": 48,
        "objectName": "PositiveIntegerValue Silver",
        "presentValue": 1},
    "networkPort": {
        "instance": 50,
        "objectName": "NetworkPort Vermillion",
        "BACnetIPUDPPort": 47808,
        "ipLength": 4,
        "ipAddress": [0, 0, 0, 0],
        "ipDefaultGateway": [0, 0, 0, 0],
        "ipDnsServer": [0, 0, 0, 0],
        "ipNumOfDns": 0,
        "ipSubnetMask": [0, 0, 0, 0],
        "FdBbmdAddressHostIp": [192, 168, 1, 4],
        "FdBbmdAddressHostType": 1,  # 0 = None, 1 = IpAddress, 2 = Name
        "FdBbmdAddressPort": 47808,
        "FdSubscriptionLifetime": 3000,
        "changesPending": False}
}

# Globals
# -----------------------------------------------------------------------------
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

lastTimeValueWasUpdated = 0


def octetStringCopy(source, destination, length, offset=0):
    for i in range(length):
        destination[i + offset] = source[i]


# Rebuilds string from ctype.c_uint_8 arrray
def rebuildString(strPointer, length):
    rebuiltStr = ""
    for i in range(0, length):
        rebuiltStr = rebuiltStr + chr(strPointer[i])
    return rebuiltStr


# Callbacks
# -----------------------------------------------------------------------------
def CallbackReceiveMessage(message, maxMessageLength, receivedConnectionString, maxConnectionStringLength,
                           receivedConnectionStringLength,
                           networkType):
    try:
        data, addr = udpSocket.recvfrom(maxMessageLength)
        # if not data:
        #     print("DEBUG: not data")
        # A message was received.
        print ("DEBUG: CallbackReceiveMessage. Message Received", addr, data, len(data) )

        # Convert the received address to the CAS BACnet Stack connection string format.
        ip_as_bytes = map(int, addr[0].split("."))
        for i in range(len(ip_as_bytes)):
            receivedConnectionString[i] = ip_as_bytes[i]
        # UDP Port
        receivedConnectionString[4] = int(addr[1] / 256)
        receivedConnectionString[5] = addr[1] % 256
        # New ConnectionString Length
        receivedConnectionStringLength[0] = 6

        # Convert the received data to a format that CAS BACnet Stack can process.
        for i in range(len(data)):
            message[i] = ord(data[i])

        # Set the network type
        networkType[0] = ctypes.c_uint8(casbacnetstack_networkType["ip"])
        return int(len(data))
    except socket.timeout:
        # No message, We are not waiting for a incoming message so our socket returns a BlockingIOError. This is normal.
        return int(0)
    except io.BlockingIOError:
        # No message, We are not waiting for a incoming message so our socket returns a BlockingIOError. This is normal.
        return int(0)
    except socket.error:
        # No message, We are not waiting for a incoming message so our socket returns a BlockingIOError. This is normal.
        return int(0)

    # Catch all
    return 0


def CallbackSendMessage(message, messageLength, connectionString, connectionStringLength, networkType, broadcast):
    # Currently we are only supporting IP
    if networkType != casbacnetstack_networkType["ip"]:
        print("Error: Unsupported network type. networkType:", networkType)
        return int(0)

    # Extract the Connection String from CAS BACnet Stack into an IP address and port.
    udpPort = connectionString[4] * 256 + connectionString[5]
    if broadcast:
        # Use broadcast IP address
        # ToDo: Get the subnet mask and apply it to the IP address
        print("DEBUG:   ToDo: Broadcast this message. Local IP: ", db["networkPort"]["ipAddress"], "Subnet: ",
              db["networkPort"]["ipSubnetMask"],
              "Broadcast IP: ????")
        ipAddress = str(connectionString[0]) + "." + str(connectionString[1]) + "." + str(connectionString[2]) + "." + \
                    str(connectionString[3])

    else:
        ipAddress = str(connectionString[0]) + "." + str(connectionString[1]) + "." + str(connectionString[2]) + "." + \
                    str(connectionString[3])

    # Extract the message from CAS BACnet Stack to a bytearray
    data = bytearray(messageLength)
    for i in range(len(data)):
        data[i] = message[i]

    # Send the message
    udpSocket.sendto(data, (ipAddress, udpPort))
    return int(messageLength)


def CallbackGetSystemTime():
    return int(time.time())


def CallbackGetPropertyReal(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                            propertyArrayIndex):
    print("CallbackGetPropertyReal", deviceInstance, objectType, objectInstance, propertyIdentifier, useArrayIndex,
          propertyArrayIndex)

    if deviceInstance == db["device"]["instance"]:
        # Check for PresentValue Property
        if propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["analogInput"] and objectInstance == db["analogInput"]["instance"]:
                value[0] = ctypes.c_float(db["analogInput"]["presentValue"])
                return True
            if objectType == bacnet_objectType["analogValue"] and objectInstance == db["analogValue"]["instance"]:
                value[0] = ctypes.c_float(db["analogValue"]["presentValue"])
                return True
        # Check for covincrement Property
        elif propertyIdentifier == bacnet_propertyIdentifier["covincrement"]:
            if objectType == bacnet_objectType["analogInput"] and objectInstance == db["analogInput"]["instance"]:
                value[0] = ctypes.c_float(db["analogInput"]["covIncrement"])
                return True
            if objectType == bacnet_objectType["analogValue"] and objectInstance == db["analogValue"]["instance"]:
                value[0] = ctypes.c_float(db["analogValue"]["covIncrement"])
                return True

    # Return false. The CAS BACnet Stack will use a default value.
    return False


def CallbackGetPropertyCharString(deviceInstance, objectType, objectInstance, propertyIdentifier, value,
                                  valueElementCount, maxElementCount,
                                  encodingType, useArrayIndex, propertyArrayIndex):
    print(
        "CallbackGetPropertyCharString", deviceInstance, objectType, objectInstance, propertyIdentifier,
        maxElementCount,
        useArrayIndex,
        propertyArrayIndex)

    if deviceInstance == db["device"]["instance"]:
        # Check for vendorname Property
        if propertyIdentifier == bacnet_propertyIdentifier["vendorname"] and objectType == bacnet_objectType["device"]:
            vendorname = db["device"]["vendorname"]
            # Convert the vendorname from a string to a format that CAS BACnet Stack can process.
            b_vendorname = vendorname.encode("utf-8")
            for i in range(len(b_vendorname)):
                value[i] = b_vendorname[i]
            # Define how long the vendorname is
            valueElementCount[0] = len(b_vendorname)
            return True
        # Check for objectname Property
        elif propertyIdentifier == bacnet_propertyIdentifier["objectname"]:
            if objectType == bacnet_objectType["device"] and objectInstance == db["device"]["instance"]:
                objectName = db["device"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["analogInput"] and objectInstance == db["analogInput"]["instance"]:
                objectName = db["analogInput"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["binaryInput"] and objectInstance == db["binaryInput"]["instance"]:
                objectName = db["binaryInput"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["multiStateInput"] \
                    and objectInstance == db["multiStateInput"]["instance"]:
                objectName = db["multiStateInput"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["analogOutput"] and objectInstance == db["analogOutput"]["instance"]:
                objectName = db["analogOutput"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["analogValue"] and objectInstance == db["analogValue"]["instance"]:
                objectName = db["analogValue"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["binaryOutput"] and objectInstance == db["binaryOutput"]["instance"]:
                objectName = db["binaryOutput"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["binaryValue"] and objectInstance == db["binaryValue"]["instance"]:
                objectName = db["binaryValue"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["multiStateOutput"] and objectInstance == db["multiStateOutput"][
                "instance"]:
                objectName = db["multiStateOutput"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["multiStateValue"] and objectInstance == db["multiStateValue"][
                "instance"]:
                objectName = db["multiStateValue"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["characterstringValue"] \
                    and objectInstance == db["characterstringValue"]["instance"]:
                objectName = db["characterstringValue"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["integerValue"] and objectInstance == db["integerValue"]["instance"]:
                objectName = db["integerValue"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["largeAnalogValue"] \
                    and objectInstance == db["largeAnalogValue"]["instance"]:
                objectName = db["largeAnalogValue"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["positiveIntegerValue"] \
                    and objectInstance == db["positiveIntegerValue"]["instance"]:
                objectName = db["positiveIntegerValue"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_objectName)
                return True
            elif objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                objectName = db["networkPort"]["objectName"]
                # Convert the Object Name from a string to a format that CAS BACnet Stack can process.
                b_objectName = objectName.encode("utf-8")
                for i in range(len(b_objectName)):
                    value[i] = b_objectName[i]
                # Define how long the Object Name  is
                valueElementCount[0] = len(b_objectName)
                return True
        # Check for PresentValue Property
        elif propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["characterstringValue"] and objectInstance == db["characterstringValue"]["instance"]:
                presentValue = db["characterstringValue"]["presentValue"]
                b_presentValue = presentValue.encode("utf-8")
                for i in range(len(b_presentValue)):
                    value[i] = b_presentValue[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_presentValue)
                return True
        # Check for StateText Property
        elif propertyIdentifier == bacnet_propertyIdentifier["statetext"]:
            if objectType == bacnet_objectType["multiStateInput"] and objectInstance == db["multiStateInput"]["instance"]:
                if useArrayIndex:
                    stateText = db["multiStateInput"]["stateText"][propertyArrayIndex - 1]
                    b_stateText = stateText.encode("utf-8")
                    for i in range(len(b_stateText)):
                        value[i] = b_stateText[i]
                    # Define how long the Object name is
                    valueElementCount[0] = len(b_stateText)
                    return True
            elif objectType == bacnet_objectType["multiStateOutput"] and objectInstance == db["multiStateOutput"]["instance"]:
                if useArrayIndex:
                    stateText = db["multiStateOutput"]["stateText"][propertyArrayIndex - 1]
                    b_stateText = stateText.encode("utf-8")
                    for i in range(len(b_stateText)):
                        value[i] = b_stateText[i]
                    # Define how long the Object name is
                    valueElementCount[0] = len(b_stateText)
                    return True
            elif objectType == bacnet_objectType["multiStateValue"] and objectInstance == db["multiStateValue"]["instance"]:
                if useArrayIndex:
                    stateText = db["multiStateValue"]["stateText"][propertyArrayIndex - 1]
                    b_stateText = stateText.encode("utf-8")
                    for i in range(len(b_stateText)):
                        value[i] = b_stateText[i]
                    # Define how long the Object name is
                    valueElementCount[0] = len(b_stateText)
                    return True
        #Check for ActiveText Property
        elif propertyIdentifier == bacnet_propertyIdentifier["activetext"]:
            if objectType == bacnet_objectType["binaryInput"] and objectInstance == db["binaryInput"]["instance"]:
                activeText = db["binaryInput"]["activeText"]
                b_activeText = activeText.encode("utf-8")
                for i in range(len(b_activeText)):
                    value[i] = b_activeText[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_activeText)
                return True
            elif objectType == bacnet_objectType["binaryValue"] and objectInstance == db["binaryValue"]["instance"]:
                activeText = db["binaryValue"]["activeText"]
                b_activeText = activeText.encode("utf-8")
                for i in range(len(b_activeText)):
                    value[i] = b_activeText[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_activeText)
                return True
        #Check for InActiveText Property
        elif propertyIdentifier == bacnet_propertyIdentifier["inactivetext"]:
            if objectType == bacnet_objectType["binaryInput"] and objectInstance == db["binaryInput"]["instance"]:
                activeText = db["binaryInput"]["inactiveText"]
                b_activeText = activeText.encode("utf-8")
                for i in range(len(b_activeText)):
                    value[i] = b_activeText[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_activeText)
                return True
            elif objectType == bacnet_objectType["binaryValue"] and objectInstance == db["binaryValue"]["instance"]:
                activeText = db["binaryValue"]["inactiveText"]
                b_activeText = activeText.encode("utf-8")
                for i in range(len(b_activeText)):
                    value[i] = b_activeText[i]
                # Define how long the Object name is
                valueElementCount[0] = len(b_activeText)
                return True

    # Return false. The CAS BACnet Stack will use a default value.
    return False


def ValueToKey(enumeration, searchValue):
    # https://www.geeksforgeeks.org/python-get-key-from-value-in-dictionary/
    for key, value in enumeration.items():
        if value == searchValue:
            return key
    return "key doesn't exist"


def CallbackGetPropertyEnumerated(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                                  propertyArrayIndex):
    print(
        "CallbackGetPropertyEnumerated", deviceInstance, objectType, objectInstance, propertyIdentifier,
        propertyArrayIndex)

    if deviceInstance == db["device"]["instance"]:
        # Check for presentValue Property
        if propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["binaryInput"] and objectInstance == db["binaryInput"]["instance"]:
                value[0] = ctypes.c_uint32(db["binaryInput"]["presentValue"])
                return True
            elif objectType == bacnet_objectType["binaryValue"] and objectInstance == db["binaryValue"]["instance"]:
                value[0] = ctypes.c_uint32(db["binaryValue"]["presentValue"])
                return True
        # Check for units Property
        elif propertyIdentifier == bacnet_propertyIdentifier["units"]:
            if ValueToKey(bacnet_objectType, objectType) in db:
                if "units" in db[ValueToKey(bacnet_objectType, objectType)]:
                    value[0] = ctypes.c_uint32(db[ValueToKey(bacnet_objectType, objectType)]["units"])
                    return True
        # Check for reliability Property
        elif propertyIdentifier == bacnet_propertyIdentifier["reliability"]:
            if ValueToKey(bacnet_objectType, objectType) in db:
                if "units" in db[ValueToKey(bacnet_objectType, objectType)]:
                    value[0] = ctypes.c_uint32(db[ValueToKey(bacnet_objectType, objectType)]["reliability"])
                    return True

            # Undefined reliability. Assume no-fault-detected (0)
            value[0] = ctypes.c_uint32(0)
            return True
        # Check for fdbbmdaddress Property, the port portion
        elif propertyIdentifier == bacnet_propertyIdentifier["fdbbmdaddress"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                value[0] = db["networkPort"]["FdBbmdAddressHostType"]
                return True

    # Return false. The CAS BACnet Stack will use a default value.
    return False

def CallbackGetPropertyBitString(deviceInstance, objectType, objectInstance, propertyIdentifier, value,
                                 valueElementCount, maxElementCount,
                                 useArrayIndex, propertyArrayIndex):
    print(
        "CallbackGetPropertyBitString", deviceInstance, objectType, objectInstance, propertyIdentifier, maxElementCount,
        useArrayIndex,
        propertyArrayIndex)
    return False


def CallbackGetPropertyBool(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                            propertyArrayIndex):
    print("CallbackGetPropertyBool", deviceInstance, objectType, objectInstance, propertyIdentifier, useArrayIndex,
          propertyArrayIndex)
    if deviceInstance == db["device"]["instance"]:
        if propertyIdentifier == bacnet_propertyIdentifier["changespending"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                value[0] = db["networkPort"]["changesPending"]
                return True
    return False


def CallbackGetPropertyDate(deviceInstance, objectType, objectInstance, propertyIdentifier, year, month, day, weekday,
                            useArrayIndex,
                            propertyArrayIndex):
    print("CallbackGetPropertyDate", deviceInstance, objectType, objectInstance, propertyIdentifier, useArrayIndex,
          propertyArrayIndex)
    return False


def CallbackGetPropertyDouble(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                              propertyArrayIndex):
    print("CallbackGetPropertyDouble", deviceInstance, objectType, objectInstance, propertyIdentifier, useArrayIndex,
          propertyArrayIndex)

    if deviceInstance == db["device"]["instance"]:
        if propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["largeAnalogValue"] and objectInstance == db["largeAnalogValue"][
                "instance"]:
                value[0] = ctypes.c_double(db["largeAnalogValue"]["presentValue"])
                return True
    return False


def CallbackGetPropertyOctetString(deviceInstance, objectType, objectInstance, propertyIdentifier, value,
                                   valueElementCount, maxElementCount,
                                   useArrayIndex, propertyArrayIndex):
    print("CallbackGetPropertyOctetString", deviceInstance, objectInstance, propertyIdentifier, maxElementCount,
          useArrayIndex, propertyArrayIndex)
    if propertyIdentifier == bacnet_propertyIdentifier["ipaddress"]:
        if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
            valueElementCount[0] = db["networkPort"]["ipLength"]
            octetStringCopy(db["networkPort"]["ipAddress"], value, valueElementCount[0])
            print("DEBUG: IN GET IP: output =" + str(value[0]) + "." + str(value[1]) + "." + str(value[2]) + "." + str(
                value[3]))
            return True
    elif propertyIdentifier == bacnet_propertyIdentifier["ipdefaultgateway"]:
        if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
            valueElementCount[0] = db["networkPort"]["ipLength"]
            octetStringCopy(db["networkPort"]["ipDefaultGateway"], value, valueElementCount[0])
            return True
    elif propertyIdentifier == bacnet_propertyIdentifier["ipsubnetmask"]:
        if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
            valueElementCount[0] = db["networkPort"]["ipLength"]
            octetStringCopy(db["networkPort"]["ipSubnetMask"], value, valueElementCount[0])
            return True
    elif propertyIdentifier == bacnet_propertyIdentifier["ipdnsserver"]:
        if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
            valueElementCount[0] = db["networkPort"]["ipNumOfDns"] * 4
            for i in range(db["networkPort"]["ipNumOfDns"]):
                octetStringCopy(db["networkPort"]["ipDnsServer"][i], value, 4, i * 4)
            return True
    elif propertyIdentifier == bacnet_propertyIdentifier["fdbbmdaddress"]:
        if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
            valueElementCount[0] = db["networkPort"]["ipLength"]
            octetStringCopy(db["networkPort"]["FdBbmdAddressHostIp"], value, valueElementCount[0])
            return True
    return False


def CallbackGetPropertyInt(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                           propertyArrayIndex):
    print("CallbackGetPropertyInt", deviceInstance, objectType, objectInstance, propertyIdentifier, useArrayIndex,
          propertyArrayIndex)

    if deviceInstance == db["device"]["instance"]:
        if propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["integerValue"] and objectInstance == db["integerValue"]["instance"]:
                value[0] = ctypes.c_int32(db["integerValue"]["presentValue"])
                return True

    return False


def CallbackGetPropertyTime(deviceInstance, objectType, objectInstance, propertyIdentifier, hour, minute, second,
                            hundrethSeconds, useArrayIndex,
                            propertyArrayIndex):
    print("CallbackGetPropertyTime", deviceInstance, objectType, objectInstance, propertyIdentifier, useArrayIndex,
          propertyArrayIndex)
    return False


def CallbackGetPropertyUInt(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                            propertyArrayIndex):
    print("CallbackGetPropertyUInt", deviceInstance, objectType, objectInstance, propertyIdentifier, useArrayIndex,
          propertyArrayIndex)
    if deviceInstance == db["device"]["instance"]:
        # Check for vendoridentifier property
        if propertyIdentifier == bacnet_propertyIdentifier["vendoridentifier"]:
            if objectType == bacnet_objectType["device"]:
                value[0] = ctypes.c_uint32(db["device"]["vendoridentifier"])
                return True
        # Check for bacnetipudpport property        
        elif propertyIdentifier == bacnet_propertyIdentifier["bacnetipudpport"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                value[0] = db["networkPort"]["BACnetIPUDPPort"]
                return True
        # Network Port Object IP DNS Server Array Size property
        elif propertyIdentifier == bacnet_propertyIdentifier["ipdnsserver"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                if useArrayIndex and propertyArrayIndex == 0:
                    value[0] = db["networkPort"]["ipNumOfDns"]
                    return True
        # Check for fdbbmdaddress property
        elif propertyIdentifier == bacnet_propertyIdentifier["fdbbmdaddress"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                if useArrayIndex and propertyArrayIndex == casbacnetstack_fdBbmdAddressOffset["port"]:
                    value[0] = db["networkPort"]["FdBbmdAddressPort"]
                    return True
        # Check for fdsubscriptionlifetime property
        elif propertyIdentifier == bacnet_propertyIdentifier["fdsubscriptionlifetime"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                value[0] = db["networkPort"]["FdSubscriptionLifetime"]
                return True
        # Check for PresentValue property
        elif propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["multiStateInput"] and objectInstance == \
                    db["multiStateInput"]["instance"]:
                value[0] = ctypes.c_uint32(db["multiStateInput"]["presentValue"])
                return True
            elif objectType == bacnet_objectType["multiStateValue"] and objectInstance == \
                    db["multiStateValue"]["instance"]:
                value[0] = ctypes.c_uint32(db["multiStateValue"]["presentValue"])
                return True
            elif objectType == bacnet_objectType["positiveIntegerValue"] and objectInstance == \
                    db["positiveIntegerValue"]["instance"]:
                value[0] = ctypes.c_uint32(db["positiveIntegerValue"]["presentValue"])
                return True
        # Check for NumberOfStates property
        elif propertyIdentifier == bacnet_propertyIdentifier["numberofstates"]:
            if objectType == bacnet_objectType["multiStateInput"] and objectInstance == \
                    db["multiStateInput"]["instance"]:
                value[0] = ctypes.c_uint32(db["multiStateInput"]["numberOfStates"])
                return True
            elif objectType == bacnet_objectType["multiStateOutput"] and objectInstance == \
                    db["multiStateOutput"]["instance"]:
                value[0] = ctypes.c_uint32(db["multiStateOutput"]["numberOfStates"])
                return True
            elif objectType == bacnet_objectType["multiStateValue"] and objectInstance == \
                    db["multiStateValue"]["instance"]:
                value[0] = ctypes.c_uint32(db["multiStateValue"]["numberOfStates"])
                return True
        # Check for StateText array size (propertyArrayIndex = 0)
        elif propertyIdentifier == bacnet_propertyIdentifier["statetext"]:
            if objectType == bacnet_objectType["multiStateInput"] and objectInstance == db["multiStateInput"]["instance"]:
                if useArrayIndex and propertyArrayIndex == 0:
                    value[0] = len(db["multiStateInput"]["stateText"])
                    return True
            elif objectType == bacnet_objectType["multiStateOutput"] and objectInstance == db["multiStateOutput"]["instance"]:
                if useArrayIndex and propertyArrayIndex == 0:
                    value[0] = len(db["multiStateOutput"]["stateText"])
                    return True
            elif objectType == bacnet_objectType["multiStateValue"] and objectInstance == db["multiStateValue"]["instance"]:
                if useArrayIndex and propertyArrayIndex == 0:
                    value[0] = len(db["multiStateValue"]["stateText"])
                    return True
    return False


def CallbackSetPropertyUInt(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                            propertyArrayIndex, priority,
                            errorCode):
    print(
        "CallbackSetPropertyUInt", deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
        propertyArrayIndex,
        priority, errorCode)
    if deviceInstance == db["device"]["instance"]:
        # Check for the fdbbmdaddress property, port portion
        if propertyIdentifier == bacnet_propertyIdentifier["fdbbmdaddress"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                db["networkPort"]["FdBbmdAddressPort"] = value
                db["networkPort"]["changesPending"] = True
                return True
        # Check for the fdsubscriptionlifetime property
        elif propertyIdentifier == bacnet_propertyIdentifier["fdsubscriptionlifetime"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                db["networkPort"]["FdSubscriptionLifetime"] = value
                db["networkPort"]["changesPending"] = True
                return True
        # Check for the PresentValue property
        elif propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["multiStateValue"] and objectInstance == db["multiStateValue"][
                "instance"]:
                db["multiStateValue"]["presentValue"] = value
                return True
    return False


def CallbackSetPropertyReal(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                            propertyArrayIndex, priority,
                            errorCode):
    print(
        "CallbackSetPropertyReal", deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
        propertyArrayIndex,
        priority, errorCode)
    if deviceInstance == db["device"]["instance"]:
        # Check for the PresentValue property
        if propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["analogInput"] and objectInstance == db["analogInput"]["instance"]:
                db["analogInput"]["presentValue"] = value
                return True
            elif objectType == bacnet_objectType["analogValue"] and objectInstance == db["analogValue"]["instance"]:
                db["analogValue"]["presentValue"] = value
                return True
        # Check for the covincrement property
        elif propertyIdentifier == bacnet_propertyIdentifier["covincrement"]:
            if objectType == bacnet_objectType["analogInput"] and objectInstance == db["analogInput"]["instance"]:
                db["analogInput"]["covIncrement"] = value
                return True
            elif objectType == bacnet_objectType["analogValue"] and objectInstance == db["analogValue"]["instance"]:
                db["analogValue"]["covIncrement"] = value
                return True
    return False


def CallbackSetPropertyEnumerated(deviceInstance, objectType, objectInstance, propertyIdentifier, value, useArrayIndex,
                                  propertyArrayIndex, priority,
                                  errorCode):
    print(
        "CallbackSetPropertyEnumerated", deviceInstance, objectType, objectInstance, propertyIdentifier, value,
        useArrayIndex,
        propertyArrayIndex,
        priority, errorCode)
    if deviceInstance == db["device"]["instance"]:
        # Check for the PresentValue property
        if propertyIdentifier == bacnet_propertyIdentifier["presentValue"]:
            if objectType == bacnet_objectType["binaryValue"] and objectInstance == db["binaryValue"]["instance"]:
                db["binaryValue"]["presentValue"] = value
                return True
    return False


def CallbackSetPropertyOctetString(deviceInstance, objectType, objectInstance, propertyIdentifier, value, length,
                                   useArrayIndex, propertyArray,
                                   priority, errorCode):
    print(
        "CallbackSetPropertyOctetString", deviceInstance, objectType, objectInstance, propertyIdentifier, value, length,
        useArrayIndex,
        propertyArray, priority, errorCode)
    if deviceInstance == db["device"]["instance"]:
        if propertyIdentifier == bacnet_propertyIdentifier["fdbbmdaddress"]:
            if objectType == bacnet_objectType["networkPort"] and objectInstance == db["networkPort"]["instance"]:
                db["networkPort"]["FdBbmdAddressHostIp"][0] = value[0]
                db["networkPort"]["FdBbmdAddressHostIp"][1] = value[1]
                db["networkPort"]["FdBbmdAddressHostIp"][2] = value[2]
                db["networkPort"]["FdBbmdAddressHostIp"][3] = value[3]
                db["networkPort"]["changesPending"] = False
                return True
    return False


def CallbackReinitializeDevice(deviceInstance, reinitializedState, password, passwordLength, errorCode):
    # Rebuild password from pointer reference
    derefedPassword = rebuildString(password, passwordLength)

    print(
        "CallbackReinitializeDevice", deviceInstance, reinitializedState, derefedPassword, passwordLength, errorCode[0])

    # This callback is called when this BACnet Server device receives a ReinitializeDevice message
    # In this callback, you will handle the reinitializedState
    # If reinitializedState = ACTIVATE_CHANGES (7) then you will apply any network port changes and store the values in
    #   non-volatile memory
    # If reinitializedState = WARM_START(1) then you will apply any network port changes, store the values in
    #   non-volatile memory, and restart the device

    # Before handling the reinitializedState, first check the password.
    # If your device does not require a password, then ignore any password passed in.
    # Otherwise, validate the password.
    #       If password invalid, missing, or incorrect: set errorCode to PasswordInvalid (26)
    # In this example, a password of 12345 is required

    # Check password before handling reinitialization
    if passwordLength == 0 or derefedPassword != "12345":
        errorCode[0] = bacnet_errorCode["password-failure"]
        return False

    # In this example, only the NetworkPort Object FdBbmdAddress and FdSubscriptionLifetime properties are writable and
    #   need to be stored in non-volatile memory.  For the purpose of this example, we will not storing these values in
    #   non-volatile memory.

    # 1. Store values that must be stored in non-volatile memory (i.e. must survive a reboot)

    # 2. Apply any Network Port values that have been written to
    # If any validation on the Network Port values fails, set errorCode to INVALID_CONFIGURATION_DATA (46)

    # 3. Set Network Port ChangesPending property to false

    # 4. Handle ReinitializedState. If ACTIVATE_CHANGES, no other action, return true
    #                               If WARM_START, prepare device for reboot, return true. and reboot
    # NOTE: Must return True first before rebooting so the stack sends the SimpleAck
    if reinitializedState == casbacnetstack_reinitializeState["state-activate-changes"]:
        db["networkPort"]["changesPending"] = False
        return True
    elif reinitializedState == casbacnetstack_reinitializeState["state-warm-start"]:
        # Flag for reboot and handle reboot after stack responds with SimpleAck
        db["networkPort"]["changesPending"] = False
        errorCode[0] = 2
        return True
    else:
        # All other states are not supported in this example
        errorCode[0] = bacnet_errorCode["optional-functionality-not-supported"]
        return False


def CallbackDeviceCommunicationControl(deviceInstance, enableDisable, password, passwordLength, useTimeDuration,
                                       timeDuration, errorCode):
    # Rebuild password from pointer reference
    derefedPassword = rebuildString(password, passwordLength)

    print("CallbackDeviceCommunicationControl", deviceInstance, enableDisable, derefedPassword, passwordLength,
          useTimeDuration, timeDuration,
          errorCode[0])

    # This callback is called when this BACnet Server device receives a DeviceCommunicationControl message
    # In this callback, you will handle the password. All other parameters are purely for logging to know
    # what parameters the DeviceCommunicationControl request had

    # To handle the password:
    # If your device does not require a password, then ignore any password passed in
    # Otherwise, validate the password
    #       If password invalid, missing, or incorrect: set errorCode to PasswordInvalid (26)
    # In this example, a password of 12345 is required

    # Check password
    if passwordLength == 0 or derefedPassword != "12345":
        errorCode[0] = bacnet_errorCode["password-failure"]
        return False

    # Return true to allow DeviceCommunicationControl logic to continue
    return True


def CallbackLogDebugMessage(message, messageLength, messageType):
    # Rebuild message from pointer reference
    derefedMessage = rebuildString(message, messageLength)
    print("CallbackLogDebugMessage", derefedMessage, messageLength, messageType)

    if derefedMessage != "" and messageLength != 0:
        print("CAS BACnet Stack DEBUG MESSAGE: ", derefedMessage)


# Main application
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("FYI: CAS BACnet Stack Python2.7 Server Example v{}".format(bacnet_server_example_python27_version))
    print("FYI: https://github.com/chipkin/BACnetServerExamplePython2.7")

    # 1. Load the CAS BACnet stack functions
    # ---------------------------------------------------------------------------
    # Load the shared library into ctypes
    libpath = pathlib.Path().absolute() / libname
    print("FYI: Libary path: ", libpath)
    CASBACnetStack = ctypes.CDLL(str(libpath), mode=ctypes.RTLD_GLOBAL)

    # Print the version information
    print("FYI: CAS BACnet Stack version: " + str(CASBACnetStack.BACnetStack_GetAPIMajorVersion()) + "." +
          str(CASBACnetStack.BACnetStack_GetAPIMinorVersion()) +
          "." + str(CASBACnetStack.BACnetStack_GetAPIPatchVersion()) + "." +
          str(CASBACnetStack.BACnetStack_GetAPIBuildVersion()))
    print("FYI: CAS BACnet Stack python adapter version:" + str(casbacnetstack_adapter_version))

    # 2. Connect the UDP resource to the BACnet Port and get network info
    # ---------------------------------------------------------------------------
    print("FYI: Connecting UDP Resource to port=[" + str(db['networkPort']['BACnetIPUDPPort']) + "]")
    HOST = ""  # Symbolic name meaning all available interfaces
    udpSocket.bind((HOST, db["networkPort"]["BACnetIPUDPPort"]))
    udpSocket.setblocking(False)

    # Load network information into database

    db["networkPort"]["ipAddress"] = [int(octet) for octet in
                                      netifaces.ifaddresses(netifaces.interfaces()[0])[netifaces.AF_INET][0][
                                          "addr"].split(".")]
    db["networkPort"]["ipSubnetMask"] = [int(octet) for octet in
                                         netifaces.ifaddresses(netifaces.interfaces()[0])[netifaces.AF_INET][0][
                                             "netmask"].split(".")]
    db["networkPort"]["ipDefaultGateway"] = [int(octet) for octet in
                                             netifaces.gateways()["default"][netifaces.AF_INET][0].split(".")]
    dnsServerOctetList = []
    for dnsServer in dns.resolver.Resolver().nameservers:
        dnsServerOctetList.append([int(octet) for octet in dnsServer.split(".")])
    db["networkPort"]["ipNumOfDns"] = len(dnsServerOctetList)
    db["networkPort"]["ipDnsServer"] = dnsServerOctetList

    print("FYI: Local IP address: ", db["networkPort"]["ipAddress"])

    # 3. Setup the callbacks
    # ---------------------------------------------------------------------------
    print("FYI: Registering the Callback Functions with the CAS BACnet Stack")

    # Note:
    # Make sure you keep references to CFUNCTYPE() objects as long as they are used from C code.
    # ctypes doesn't, and if you don"t, they may be garbage collected, crashing your program when
    # a callback is made
    #
    # Because of garbage collection, the pyCallback**** functions need to stay in scope.
    
    # Core Callbacks
    pyCallbackReceiveMessage = fpCallbackReceiveMessage(CallbackReceiveMessage)
    CASBACnetStack.BACnetStack_RegisterCallbackReceiveMessage(pyCallbackReceiveMessage)
    pyCallbackSendMessage = fpCallbackSendMessage(CallbackSendMessage)
    CASBACnetStack.BACnetStack_RegisterCallbackSendMessage(pyCallbackSendMessage)
    pyCallbackGetSystemTime = fpCallbackGetSystemTime(CallbackGetSystemTime)
    CASBACnetStack.BACnetStack_RegisterCallbackGetSystemTime(pyCallbackGetSystemTime)

    # GetProperty Callbacks
    pyCallbackGetPropertyBitString = fpCallbackGetPropertyBitString(CallbackGetPropertyBitString)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyBitString(pyCallbackGetPropertyBitString)
    pyCallbackGetPropertyBool = fpCallbackGetPropertyBool(CallbackGetPropertyBool)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyBool(pyCallbackGetPropertyBool)
    pyCallbackGetPropertyCharString = fpCallbackGetPropertyCharString(CallbackGetPropertyCharString)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyCharacterString(pyCallbackGetPropertyCharString)
    pyCallbackGetPropertyDate = fpCallbackGetPropertyDate(CallbackGetPropertyDate)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyDate(pyCallbackGetPropertyDate)
    pyCallbackGetPropertyDouble = fpCallbackGetPropertyDouble(CallbackGetPropertyDouble)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyDouble(pyCallbackGetPropertyDouble)
    pyCallbackGetPropertyEnum = fpCallbackGetPropertyEnum(CallbackGetPropertyEnumerated)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyEnumerated(pyCallbackGetPropertyEnum)
    pyCallbackGetPropertyOctetString = fpCallbackGetPropertyOctetString(CallbackGetPropertyOctetString)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyOctetString(pyCallbackGetPropertyOctetString)
    pyCallbackGetPropertyInt = fpCallbackGetPropertyInt(CallbackGetPropertyInt)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertySignedInteger(pyCallbackGetPropertyInt)
    pyCallbackGetPropertyReal = fpCallbackGetPropertyReal(CallbackGetPropertyReal)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyReal(pyCallbackGetPropertyReal)
    pyCallbackGetPropertyTime = fpCallbackGetPropertyTime(CallbackGetPropertyTime)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyTime(pyCallbackGetPropertyTime)
    pyCallbackGetPropertyUInt = fpCallbackGetPropertyUInt(CallbackGetPropertyUInt)
    CASBACnetStack.BACnetStack_RegisterCallbackGetPropertyUnsignedInteger(pyCallbackGetPropertyUInt)

    # SetProperty Callbacks
    pyCallbackSetPropertyEnumerated = fpCallbackSetPropertyEnum(CallbackSetPropertyEnumerated)
    CASBACnetStack.BACnetStack_RegisterCallbackSetPropertyEnumerated(pyCallbackSetPropertyEnumerated)   
    pyCallbackSetPropertyOctetString = fpCallbackSetPropertyOctetString(CallbackSetPropertyOctetString)
    CASBACnetStack.BACnetStack_RegisterCallbackSetPropertyOctetString(pyCallbackSetPropertyOctetString)
    pyCallbackSetPropertyReal = fpCallbackSetPropertyReal(CallbackSetPropertyReal)
    CASBACnetStack.BACnetStack_RegisterCallbackSetPropertyReal(pyCallbackSetPropertyReal)
    pyCallbackSetPropertyUInt = fpCallbackSetPropertyUInt(CallbackSetPropertyUInt)
    CASBACnetStack.BACnetStack_RegisterCallbackSetPropertyUnsignedInteger(pyCallbackSetPropertyUInt)

    # BACnet Service Callbacks
    pyCallbackReinitializeDevice = fpCallbackReinitializeDevice(CallbackReinitializeDevice)
    CASBACnetStack.BACnetStack_RegisterCallbackReinitializeDevice(pyCallbackReinitializeDevice)
    pyCallbackDeviceCommunicationControl = fpCallbackDeviceCommunicationControl(CallbackDeviceCommunicationControl)
    CASBACnetStack.BACnetStack_RegisterCallbackDeviceCommunicationControl(pyCallbackDeviceCommunicationControl)
    # pyCallbackLogDebugMessage = fpCallbackLogDebugMessage(CallbackLogDebugMessage)
    # CASBACnetStack.BACnetStack_RegisterCallbackLogDebugMessage(pyCallbackLogDebugMessage)

    # 4. Setup the BACnet device
    # ---------------------------------------------------------------------------
    print("FYI: Setting up server Device. device.instance=[" + str(db['device']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddDevice(db["device"]["instance"]):
        print("Error: Failed to add Device")
        exit()

    # Enable optional BACnet services.
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["readPropertyMultiple"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["writeProperty"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["writePropertyMultiple"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["subscribeCov"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["subscribeCovProperty"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["reinitializeDevice"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["deviceCommunicationControl"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["iAm"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["confirmedTextMessage"], True)
    CASBACnetStack.BACnetStack_SetServiceEnabled(db["device"]["instance"], casbacnetstack_service["unconfirmedTextMessage"], True)

    # Add Objects
    # ---------------------------------------

    # AnalogInput (AI)
    # ---------------------------------------
    print("FYI: Adding AnalogInput. AnalogInput.instance=[" + str(db['analogInput']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["analogInput"],
                                                db["analogInput"]["instance"]):
        print("Error: Failed to add analogInput")
        exit()

    # Enable optional properties
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["analogInput"],
                                                  db["analogInput"]["instance"],
                                                  bacnet_propertyIdentifier["covincrement"], True)
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["analogInput"],
                                                  db["analogInput"]["instance"],
                                                  bacnet_propertyIdentifier["reliability"], True)

    # Make analogInput subscribable
    CASBACnetStack.BACnetStack_SetPropertySubscribable(db["device"]["instance"], bacnet_objectType["analogInput"],
                                                    db["analogInput"]["instance"],
                                                    bacnet_propertyIdentifier["presentValue"], True)

    # Make covIncrement writable
    CASBACnetStack.BACnetStack_SetPropertyWritable(db["device"]["instance"], bacnet_objectType["analogInput"],
            db["analogInput"]["instance"], bacnet_propertyIdentifier["covincrement"], True)

    # BinaryInput (BI)
    # ---------------------------------------
    print("FYI: Adding BinaryInput. BinaryInput.instance=[" + str(db['binaryInput']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["binaryInput"],
                                                db["binaryInput"]["instance"]):
        print("Error: Failed to add binaryInput")
        exit()

    # Enable Optional Properties
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["binaryInput"],
                                                  db["binaryInput"]["instance"],
                                                  bacnet_propertyIdentifier["activetext"], True)
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["binaryInput"],
                                                  db["binaryInput"]["instance"],
                                                  bacnet_propertyIdentifier["inactivetext"], True)

    # Make binaryInput subscribable
    CASBACnetStack.BACnetStack_SetPropertySubscribable(db["device"]["instance"], bacnet_objectType["binaryInput"],
                                                    db["binaryInput"]["instance"],
                                                    bacnet_propertyIdentifier["presentValue"], True)

    # MultiStateInput (MSI)
    # ---------------------------------------
    print("FYI: Adding MultiStateInput. MultiStateInput.instance=[" + str(db['multiStateInput']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["multiStateInput"],
                                                db["multiStateInput"]["instance"]):
        print("Error: Failed to add MultiStateInput")
        exit()

    # Enable Optional Properties
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["multiStateInput"],
                                                  db["multiStateInput"]["instance"],
                                                  bacnet_propertyIdentifier["statetext"], True)

    # Make multiStateInput subscribable
    CASBACnetStack.BACnetStack_SetPropertySubscribable(db["device"]["instance"], bacnet_objectType["multiStateInput"],
                                                    db["multiStateInput"]["instance"],
                                                    bacnet_propertyIdentifier["presentValue"], True)

    # AnalogOutput (AO)
    # ---------------------------------------
    print("FYI: Adding analogOutput. analogOutput.instance=[" + str(db['analogOutput']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["analogOutput"],
                                                db["analogOutput"]["instance"]):
        print("Error: Failed to add analogOutput")
        exit()

    # AnalogValue (AV)
    # ---------------------------------------
    print("FYI: Adding analogValue. analogValue.instance=[" + str(db['analogValue']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["analogValue"],
                                                db["analogValue"]["instance"]):
        print("Error: Failed to add analogValue")
        exit()

    # Enable optional properties
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["analogValue"],
                                                  db["analogValue"]["instance"],
                                                  bacnet_propertyIdentifier["reliability"], True)
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["analogValue"],
                                                  db["analogValue"]["instance"],
                                                  bacnet_propertyIdentifier["covincrement"], True)
    # Make analogValue PresentValue Writable
    if not CASBACnetStack.BACnetStack_SetPropertyWritable(db["device"]["instance"], bacnet_objectType["analogValue"],
            db["analogValue"]["instance"], bacnet_propertyIdentifier["presentValue"], True):
        print("Error: Failed to set analogValue.presentValue to writable")

    # Make covIncrement writable
    CASBACnetStack.BACnetStack_SetPropertyWritable(db["device"]["instance"], bacnet_objectType["analogValue"],
            db["analogValue"]["instance"], bacnet_propertyIdentifier["covincrement"], True)
   
    # Make analogValue subscribable
    CASBACnetStack.BACnetStack_SetPropertySubscribable(db["device"]["instance"], bacnet_objectType["analogValue"],
                                                    db["analogValue"]["instance"],
                                                    bacnet_propertyIdentifier["presentValue"], True)

    # BinaryOutput (BO)
    # ---------------------------------------
    print("FYI: Adding binaryOutput. binaryOutput.instance=[" + str(db['binaryOutput']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["binaryOutput"],
                                                db["binaryOutput"]["instance"]):
        print("Error: Failed to add binaryOutput")
        exit()

    # BinaryValue (BV)
    # ---------------------------------------
    print("FYI: Adding binaryValue. binaryValue.instance=[" + str(db['binaryValue']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["binaryValue"],
                                                db["binaryValue"]["instance"]):
        print("Error: Failed to add binaryValue")
        exit()

    # Enable Optional Properties
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["binaryValue"],
                                                  db["binaryValue"]["instance"],
                                                  bacnet_propertyIdentifier["activetext"], True)
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["binaryValue"],
                                                  db["binaryValue"]["instance"],
                                                  bacnet_propertyIdentifier["inactivetext"], True)

    # Make binaryValue PresentValue Writable
    if not CASBACnetStack.BACnetStack_SetPropertyWritable(db["device"]["instance"], bacnet_objectType["binaryValue"],
                                                          db["binaryValue"]["instance"],
                                                          bacnet_propertyIdentifier["presentValue"], True):
        print("Error: Failed to set binaryValue.presentValue to writable")

    # Make binaryValue subscribable
    CASBACnetStack.BACnetStack_SetPropertySubscribable(db["device"]["instance"], bacnet_objectType["binaryValue"],
                                                    db["binaryValue"]["instance"],
                                                    bacnet_propertyIdentifier["presentValue"], True)   

    # MultiStateOutput (MSO)
    # ---------------------------------------
    print("FYI: Adding multiStateOutput. multiStateOutput.instance=[" + str(db['multiStateOutput']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["multiStateOutput"],
                                                db["multiStateOutput"]["instance"]):
        print("Error: Failed to add multiStateOutput")
        exit()

    # Enable Optional Properties
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["multiStateOutput"],
                                                  db["multiStateOutput"]["instance"],
                                                  bacnet_propertyIdentifier["statetext"], True)

    # MultiStateValue (MSV)
    # ---------------------------------------
    print("FYI: Adding multiStateOutput. multiStateValue.instance=[" + str(db['multiStateValue']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["multiStateValue"],
                                                db["multiStateValue"]["instance"]):
        print("Error: Failed to add multiStateValue")
        exit()
    
    # Enable Optional Properties
    CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["multiStateValue"],
                                                  db["multiStateValue"]["instance"],
                                                  bacnet_propertyIdentifier["statetext"], True)

    # Make  multiStateValue PresentValue Writable
    if not CASBACnetStack.BACnetStack_SetPropertyWritable(db["device"]["instance"],
                                                          bacnet_objectType["multiStateValue"],
                                                          db["multiStateValue"]["instance"],
                                                          bacnet_propertyIdentifier["presentValue"], True):
        print ("Error: Failed to set multiStateValue.presentValue to writable")

    # Make multiStateValue subscribable
    CASBACnetStack.BACnetStack_SetPropertySubscribable(db["device"]["instance"], bacnet_objectType["multiStateValue"],
                                                    db["multiStateValue"]["instance"],
                                                    bacnet_propertyIdentifier["presentValue"], True)    

    # CharacterStringValue (CSV)
    # ---------------------------------------
    print("FYI: Adding characterstringValue. characterstringValue.instance=[" + str(
        db['characterstringValue']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["characterstringValue"],
                                                db["characterstringValue"]["instance"]):
        print("Error: Failed to add characterstringValue")
        exit()

    # IntegerValue (IV)
    # ---------------------------------------
    print("FYI: Adding integerValue. integerValue.instance=[" + str(db['integerValue']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["integerValue"],
                                                db["integerValue"]["instance"]):
        print("Error: Failed to add integerValue")
        exit()

    # LargeAnalogValue (LAV)
    # ---------------------------------------
    print("FYI: Adding largeAnalogValue. largeAnalogValue.instance=[" + str(db['largeAnalogValue']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["largeAnalogValue"],
                                                db["largeAnalogValue"]["instance"]):
        print("Error: Failed to add largeAnalogValue")
        exit()

    # PositiveIntegerValue (PIV)
    # ---------------------------------------
    print("FYI: Adding positiveIntegerValue. positiveIntegerValue.instance=[" + str(
        db['positiveIntegerValue']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddObject(db["device"]["instance"], bacnet_objectType["positiveIntegerValue"],
                                                db["positiveIntegerValue"]["instance"]):
        print("Error: Failed to add positiveIntegerValue")
        exit()

    # NetworkPort (NP)
    # ---------------------------------------
    print("FYI: Adding networkPort. networkPort.instance=[" + str(db['networkPort']['instance']) + "]")
    if not CASBACnetStack.BACnetStack_AddNetworkPortObject(db["device"]["instance"], db["networkPort"]["instance"],
                                                           casbacnetstack_networkType["ipv4"],
                                                           casbacnetstack_protocolLevel["bacnet-application"],
                                                           casbacnetstack_network_port_lowest_protocol_level):
        print("Error: Failed to add networkPort")
        exit()
    if not CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["networkPort"],
                                                         db["networkPort"]["instance"],
                                                         bacnet_propertyIdentifier["fdbbmdaddress"], True):
        print("Error: Failed to enable fdBbmdAddress")
    if not CASBACnetStack.BACnetStack_SetPropertyEnabled(db["device"]["instance"], bacnet_objectType["networkPort"],
                                                         db["networkPort"]["instance"],
                                                         bacnet_propertyIdentifier["fdsubscriptionlifetime"], True):
        print("Error: Failed to enable fdSubscriptionLifetime")
    if not CASBACnetStack.BACnetStack_SetPropertyWritable(db["device"]["instance"], bacnet_objectType["networkPort"],
                                                          db["networkPort"]["instance"],
                                                          bacnet_propertyIdentifier["fdbbmdaddress"], True):
        print("Error: Failed to set fdBbmdAddress to writable")
    if not CASBACnetStack.BACnetStack_SetPropertyWritable(db["device"]["instance"], bacnet_objectType["networkPort"],
                                                          db["networkPort"]["instance"],
                                                          bacnet_propertyIdentifier["fdsubscriptionlifetime"], True):
        print("Error: Failed to set fdSubscriptionLifetime to writable")

    # 5. Send I-Am of this device
    # ---------------------------------------------------------------------------
    print("FYI: Sending I-AM broadcast")
    addressString = (ctypes.c_uint8 * 6)()
    octetStringCopy(db["networkPort"]["ipAddress"], addressString, 4)
    addressString[4] = int(db["networkPort"]["BACnetIPUDPPort"] / 256)
    addressString[5] = db["networkPort"]["BACnetIPUDPPort"] % 256

    if not CASBACnetStack.BACnetStack_SendIAm(ctypes.c_uint32(db["device"]["instance"]),
                                              ctypes.cast(addressString, ctypes.POINTER(ctypes.c_uint8)),
                                              ctypes.c_uint8(6), ctypes.c_uint8(casbacnetstack_networkType["ip"]),
                                              ctypes.c_bool(True),
                                              ctypes.c_uint16(65535), None, ctypes.c_uint8(0)):
        print("Error: Failed to send I-Am")

    # 6. Start the main loop
    # ---------------------------------------------------------------------------
    print("FYI: Entering main loop...")
    while True:
        # Call the DLLs loop function which checks for messages and processes them.
        CASBACnetStack.BACnetStack_Tick()

        # Sleep between loops. Give some time to other application
        time.sleep(0.1)

        # Every x seconds increment the AnalogInput presentValue property by 0.1
        if lastTimeValueWasUpdated + 1 < time.time():
            lastTimeValueWasUpdated = time.time()
            db["analogInput"]["presentValue"] += 0.1
            # Notify the stack that this data point was updated so the stack can check for logic
            # 		that may need to run on the data.  Example: check if COV (change of value) occurred.
            if CASBACnetStack.BACnetStack_ValueUpdated is not None:
                CASBACnetStack.BACnetStack_ValueUpdated(db["device"]["instance"], bacnet_objectType["analogInput"],
                                                        db["analogInput"]["instance"],
                                                        bacnet_propertyIdentifier["presentValue"])
            print("FYI: Updating AnalogInput (0) PresentValue: ", round(db["analogInput"]["presentValue"], 1))
