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

DOMAIN = "xteng_gateway_2.4g"
# 配置串行端口参数
PORT = '/dev/ttyUSB0'  # 串行端口名称，根据你的设备进行修改
BAUDRATE = 115200  # 波特率，根据你的设备进行修改
sendBuffer = []
getBuffer = []
entities = dict()
deviceMap = dict()
SER = serial.Serial(PORT, BAUDRATE, timeout=0.5)

logger = logging.getLogger(__name__)

def setup(hass: HomeAssistant, config: ConfigType):
    # with open("/config/custom_components/xteng_gateway/log.txt", "+a", encoding="utf-8") as file:
    #    file.write(str(strftime('%Y-%m-%d %H:%M:%S  ', localtime())))

    with open("/config/custom_components/xteng_gateway_2.4g/data.json", "r", encoding="utf-8") as data:
        result = json.load(data)

    hass.data[DOMAIN] = {
        "devices": result["deviceList"],
        "scenes": result["sceneList"],
        "send": sendBuffer,
        "entities": entities,
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
                entities[deviceId].state_updated_callback(devStatus)
                
def uart_send():
    while True:
        if sendBuffer:
            packet = sendBuffer.pop(0)
            SER.flush()
            SER.write(packet)
            SER.flush()
