"""Platform for light integration."""
from __future__ import annotations
import math

from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN 

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN

ON_CODE = 0x01
OFF_CODE = 0x02
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
    devices = hass.data[DOMAIN]['devices']
    
    light_style_list = ['21337013']
    entities = []
    for device in devices:
        # 设备类型为灯光
        style = str(device["factoryCode"]) + str(device["factorySubtype"]) + str(device["factoryType"])
        if style in light_style_list:
            entity = XtLightEntity(device, hass)
            hass.data[DOMAIN]['entities'][entity.unique_id] = entity
            entities.append(entity)
            
    # Add entities
    add_entities(entities)


class XtLightBaseEntity(LightEntity):
    """Representation of a Custom light."""

    def __init__(self, light, hass):
        """Initialize the light."""
        self._hass = hass
        self._light = light
        self._name = light['deviceName']
        self._id = light['deviceId']
        self._state = eval(light['wsDevData'])['power_switch'] == '1'
        self._should_poll = False  # 设置为 False，表示不使用轮询
        
        self.location = bytearray(bytes.fromhex(light['deviceId']))
    #     self.on_packet = self.set_packet(ON_CODE)
    #     self.off_packet = self.set_packet(OFF_CODE)

    # def set_packet(self, code):
    #     order = bytearray(b'\x00' * 0x0C)
    #     order[0] = 0x0B
    #     order[1] = 0x01
    #     order[2] = code
    #     order[5] = 0x0A
    #     order[6] = 0x0A

    #     packet = bytearray([0x55, 0x10, 0x01])
    #     packet.append(len(self.location))
    #     packet.extend(self.location)
    #     packet.append(len(order))
    #     packet.extend(order)
    #     packet.append(0xAA)
    #     return packet

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
    
    # def state_updated_callback(self, new_state):
    #     self._state = new_state.get('power_switch') == 1
    #     self._brightness = new_state.get('brightness')
    #     self._color_temp_kelvin = new_state.get('color_temp')
    #     self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        _data = self._hass.data[DOMAIN]

        # _data["send_list"].append(self.off_packet)
        self._state = False
        self.schedule_update_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        _data = self._hass.data[DOMAIN]

        # _data["send_list"].append(self.on_packet)
        self._state = True
        self.schedule_update_ha_state()


class XtLightEntity(XtLightBaseEntity):
    """Representation of a Custom light."""

    def __init__(self, light, hass):
        """Initialize the light."""
        super().__init__(light, hass)
        self._brightness = eval(light['wsDevData'])['brightness']
        self._color_temp_kelvin = eval(light['wsDevData'])['color_temp']
        
        self._attr_min_color_temp_kelvin = MIN_COLOR_TEMP_KELVIN
        self._attr_max_color_temp_kelvin = MAX_COLOR_TEMP_KELVIN
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_supported_color_modes = set()
        self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)

        self.location = bytearray(bytes.fromhex(light['deviceId']))
        self.on_packet = self.set_packet(ON_CODE)
        self.off_packet = self.set_packet(OFF_CODE)

    def set_packet(self, code):
        order = bytearray(b'\x00' * 0x0C)
        order[0] = 0x0B
        order[1] = 0x01
        order[2] = code
        order[5] = 0x0A
        order[6] = 0x0A

        packet = bytearray([0x55, 0x10, 0x01])
        packet.append(len(self.location))
        packet.extend(self.location)
        packet.append(len(order))
        packet.extend(order)
        packet.append(0xAA)
        return packet
    
    def state_updated_callback(self, new_state):
        self._state = new_state.get('power_switch') == 1
        self._brightness = new_state.get('brightness')
        self._color_temp_kelvin = new_state.get('color_temp')
        self.schedule_update_ha_state()
    
    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the CT color value in Kelvin."""
        return round(self._color_temp_kelvin * ((MAX_COLOR_TEMP_KELVIN-MIN_COLOR_TEMP_KELVIN) / 10) + MIN_COLOR_TEMP_KELVIN)

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return round(self._brightness * (255 / 10))
    
    def set_color_temp_and_brightness(self, kwargs):
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = round(kwargs[ATTR_BRIGHTNESS] / 255 * 10)
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._color_temp_kelvin = round((kwargs[ATTR_COLOR_TEMP_KELVIN] - MIN_COLOR_TEMP_KELVIN) / (MAX_COLOR_TEMP_KELVIN-MIN_COLOR_TEMP_KELVIN) * 10)


    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        self.set_color_temp_and_brightness(kwargs)

        _data = self._hass.data[DOMAIN]

        self.off_packet[3] = self._brightness
        self.off_packet[4] = self._color_temp_kelvin

        _data["send"].append(self.off_packet)
        self._state = False
        self.schedule_update_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        self.set_color_temp_and_brightness(kwargs)
        
        _data = self._hass.data[DOMAIN]

        self.on_packet[3] = self._brightness
        self.on_packet[4] = self._color_temp_kelvin

        _data["send"].append(self.on_packet)
        self._state = True
        self.schedule_update_ha_state()
