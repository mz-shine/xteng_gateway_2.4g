"""Platform for light integration."""
from __future__ import annotations
import math

from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN 

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN

ON_CODE = 0xC10101
OFF_CODE = 0xC10102
MIN_COLOR_TEMP_KELVIN = 2700
MAX_COLOR_TEMP_KELVIN = 6500

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the custom light platform."""
    # Get data that you put in hass.data[DOMAIN] in your __init__.py
    lights = hass.data[DOMAIN]['devices']
    
    light_style_list = ['8226113']
    _lights = []
    for light in lights:
        # 设备类型为灯光
        light_style = str(light["factoryCode"]) + str(light["factorySubtype"]) + str(light["factoryType"])
        if light_style in light_style_list:
            light_class = XtLight(light, hass)
            light_id = light['deviceId']
            hass.data[DOMAIN]['xteng_dict'][light_id] = light_class
            _lights.append(light_class)
            
    # Add entities
    add_entities(_lights)

class XtLight(LightEntity):
    """Representation of a Custom light."""

    def __init__(self, light, hass):
        """Initialize the light."""
        self._hass = hass
        self._light = light
        self._name = light['deviceName']
        self._id = light['deviceId']
        self._state = eval(light['wsDevData'])['power_switch'] == '1'
        self._brightness = eval(light['wsDevData'])['brightness']
        self._color_temp_kelvin = eval(light['wsDevData'])['color_temp']
        self._should_poll = False  # 设置为 False，表示不使用轮询
        
        self._attr_min_color_temp_kelvin = MIN_COLOR_TEMP_KELVIN
        self._attr_max_color_temp_kelvin = MAX_COLOR_TEMP_KELVIN
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_supported_color_modes = set()
        self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)

    @property
    def name(self):
        """Return the name of the light."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state
    
    @property
    def should_poll(self):
        # 返回 False，这样 Home Assistant 就不会轮询这个实体
        return self._should_poll
    
    def state_updated_callback(self, new_state):
        self._state = new_state.get('power_switch') == 1
        self._brightness = new_state.get('brightness')
        self._color_temp_kelvin = new_state.get('color_temp')
        self.schedule_update_ha_state()
    
    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the CT color value in Kelvin."""
        return round(self._color_temp_kelvin * ((MAX_COLOR_TEMP_KELVIN-MIN_COLOR_TEMP_KELVIN) / 100) + MIN_COLOR_TEMP_KELVIN)

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return round(self._brightness * (255 / 100))

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = round(kwargs[ATTR_BRIGHTNESS] / 255 * 100)
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._color_temp_kelvin = round((kwargs[ATTR_COLOR_TEMP_KELVIN] - MIN_COLOR_TEMP_KELVIN) / (MAX_COLOR_TEMP_KELVIN-MIN_COLOR_TEMP_KELVIN) * 100)

        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0:3] = OFF_CODE.to_bytes(3, 'big')
        packet_data[3] = self._brightness.to_bytes(1, 'big')[0]
        packet_data[4] = self._color_temp_kelvin.to_bytes(1, 'big')[0]
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x01,
            "LOCATION": bytearray(bytes.fromhex(self._id)),
            "DATA": packet_data
        })
        packet_end = bytearray(b'\xF5' * 17)
        packet_end[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x02,
            "LOCATION": bytearray(bytes.fromhex(self._id)),
            "DATA": packet_end
        })
        self._state = False
        self.schedule_update_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = round(kwargs[ATTR_BRIGHTNESS] / 255 * 100)
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._color_temp_kelvin = round((kwargs[ATTR_COLOR_TEMP_KELVIN] - MIN_COLOR_TEMP_KELVIN) / (MAX_COLOR_TEMP_KELVIN-MIN_COLOR_TEMP_KELVIN) * 100)

        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0:3] = ON_CODE.to_bytes(3, 'big')
        packet_data[3] = self._brightness.to_bytes(1, 'big')[0]
        packet_data[4] = self._color_temp_kelvin.to_bytes(1, 'big')[0]
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x01,
            "LOCATION": bytearray(bytes.fromhex(self._id)),
            "DATA": packet_data
        })
        packet_end = bytearray(b'\xF5' * 17)
        packet_end[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x02,
            "LOCATION": bytearray(bytes.fromhex(self._id)),
            "DATA": packet_end
        })
        self._state = True
        self.schedule_update_ha_state()
