"""Platform for switch integration."""
from __future__ import annotations
import re
from time import localtime, strftime

from homeassistant.components.switch import SwitchEntity

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN

ON_CODE = 0x6050
OFF_CODE = 0x6150

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    # 加载JSON数据
    devices = hass.data[DOMAIN]['devices']

    switch_style_list = ['822610001193', '822610002193', '822610003193']
    entities = []
    for device in devices:
        style = str(device["factoryCode"]) + str(device["factorySubtype"]) + str(device["factoryType"])
        # 一位开关
        if style == switch_style_list[0]:
            switch_name = device["deviceName"]
            wsDevData = eval(device["wsDevData"])
            switch_state = wsDevData.get(f'switch_1', 0)

            switch_class = XtSwitchEntity(device, device['deviceId'], 'switch_name_1', switch_name, switch_state, hass)
            switch_id = device['deviceId']
            hass.data[DOMAIN]['xteng_dict'][switch_id] = switch_class
            entities.append(switch_class)
        # 无线二位开关
        elif style == switch_style_list[1]:
            uiRemark = eval(device["uiRemark"])
            wsDevData = eval(device["wsDevData"])
            for i in range(1, 3):
                switch_name = uiRemark.get(f'switch_name_{i}', f'switch_{i}')
                switch_state = wsDevData.get(f'switch_{i}', 0)

                switch_class = XtSwitchEntity(device, device['deviceId'], 'switch_name_1', switch_name, switch_state, hass)
                switch_id = device['deviceId']
                hass.data[DOMAIN]['xteng_dict'][switch_id] = switch_class
                entities.append(switch_class)
        # 无线三位开关
        elif style == switch_style_list[2]:
            uiRemark = eval(device["uiRemark"])
            wsDevData = eval(device["wsDevData"])
            for i in range(1, 4):
                switch_name = uiRemark.get(f'switch_name_{i}', f'switch_{i}')
                switch_state = wsDevData.get(f'switch_{i}', 0)

                switch_class = XtSwitchEntity(device, device['deviceId'], 'switch_name_1', switch_name, switch_state, hass)
                switch_id = device['deviceId']
                hass.data[DOMAIN]['xteng_dict'][switch_id] = switch_class
                entities.append(switch_class)
    # 将实体添加到Home Assistant
    add_entities(entities)

class XtSwitchEntity(SwitchEntity):
    def __init__(self, switch, device_id, switch_number, switch_name, initial_state, hass):
        self._hass = hass
        self._switch = switch
        self._device_id = device_id
        self._switch_number = switch_number
        self._name = switch_name
        self._switch_number_bytes = bytearray(bytes.fromhex('C10' + re.search(r'\d', switch_number).group()))
        self._is_on = initial_state
        # 使用 device_id 和 switch_number 创建唯一标识符
        self._id = f"{device_id}_{switch_number}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0:2] = self._switch_number_bytes
        packet_data[2:4] = ON_CODE.to_bytes(2, 'big')
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x01,
            "LOCATION": bytearray(bytes.fromhex(self._device_id)),
            "DATA": packet_data
        })
        self._is_on = True
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0:2] = self._switch_number_bytes
        packet_data[2:4] = OFF_CODE.to_bytes(2, 'big')
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x01,
            "LOCATION": bytearray(bytes.fromhex(self._device_id)),
            "DATA": packet_data
        })
        self._is_on = False
        self.schedule_update_ha_state()
