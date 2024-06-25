"""Example Lights integration."""
from __future__ import annotations
import logging
import random
import socket
import threading
from time import localtime, strftime
import serial
import json
import os

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "xteng_gateway"
# 配置串行端口参数
PORT = '/dev/ttyAMA0'  # 串行端口名称，根据你的设备进行修改
BAUDRATE = 500000  # 波特率，根据你的设备进行修改
sendBuffer = []
getBuffer = []
xtengDict = dict()
deviceMap = dict()
SER = serial.Serial(PORT, BAUDRATE, timeout=0.5)

logger = logging.getLogger(__name__)

def setup(hass: HomeAssistant, config: ConfigType):
    # with open("/config/custom_components/xteng_gateway/log.txt", "+a", encoding="utf-8") as file:
    #    file.write(str(strftime('%Y-%m-%d %H:%M:%S  ', localtime())))

    with open("/config/custom_components/xteng_gateway/data.json", "r", encoding="utf-8") as data:
        result = json.load(data)

    hass.data[DOMAIN] = {
        "devices": result["deviceList"],
        "scenes": result["sceneList"],
        "send_list": sendBuffer,
        "xteng_dict": xtengDict,
        "get_buffer": getBuffer
    }
    
    for device in result["sceneDeviceList"]:
        deviceMap[device["sceneNo"]] = deviceMap.get(device["sceneNo"], [])
        deviceMap[device["sceneNo"]].append(device)

    threading.Thread(target=uart_send, daemon=True).start()
    threading.Thread(target=uart_get, daemon=True).start()

    return True


def uart_get():
    while True:
        if getBuffer:
            id = getBuffer.pop(0)
            mapper = deviceMap[id]
            for dev in mapper:
                deviceId = dev["deviceId"]
                devStatus = eval(dev["devStatus"])
                xtengDict[deviceId].state_updated_callback(devStatus)

                
def uart_send():
    seq_num = random.randint(0x01, 0xFF)  # 流水号1

    while True:
        if sendBuffer:
            # {"PACKET_ID": _, "ORDER": _, "LOCATION": _, "DATA": _}
            data = sendBuffer.pop(0)
            seq_num = (seq_num + 1) % (0xFF + 1)
            packet = bytearray([0x55, 0x1E, 0xFF, data["PACKET_ID"], 0x55, 0xA1, seq_num, 0x64, data["ORDER"]])
            packet.extend(data["LOCATION"])
            packet.extend(data["DATA"])
            SER.flush()
            SER.write(packet)
            SER.flush()

            
def find_termination(buffer, terminator):
    """在缓冲区中查找终止符的位置"""
    position = buffer.find(terminator)
    return position
