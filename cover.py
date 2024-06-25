"""Platform for light integration."""
from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverDeviceClass

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the custom light platform."""
    # Get data that you put in hass.data[DOMAIN] in your __init__.py
    covers = hass.data[DOMAIN]['devices']

    cover_style_list = ['25664']
    _covers = []
    for cover in covers:
        # 设备类型为灯光
        cover_style = str(cover["factoryCode"]) + str(cover["factorySubtype"]) + str(cover["factoryType"])
        if cover_style in cover_style_list:
            cover_class = XtCover(cover, hass)
            cover_id = cover['deviceId']
            hass.data[DOMAIN]['xteng_dict'][cover_id] = cover_class
            _covers.append(cover_class)

    # Add entities
    add_entities(_covers)


class XtCover(CoverEntity):
    def __init__(self, cover, hass):
        self._hass = hass
        self._cover = cover
        self._name = cover['deviceName']
        self._id = cover['deviceId']
        self._state = 'on' if eval(cover['wsDevData'])['power_switch'] == '1' else 'off'
        self._position = eval(cover['wsDevData'])['position']
        self._attr_device_class = CoverDeviceClass.CURTAIN

    @property
    def name(self):
        """Return the name of the light."""
        return self._name
    
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id
    
    @property
    def current_cover_position(self):
        return self._position

    @property
    def is_closed(self):
        return self._state
    
    def state_updated_callback(self, new_state):
        self._state = new_state.get('model') == 2
        self.schedule_update_ha_state()

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0] = 0x01
        packet_data[1] = 0x01
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x01,
            "LOCATION": bytearray(bytes.fromhex(self._id)),
            "DATA": packet_data
        })
        self._state = False
        self.schedule_update_ha_state()

    async def async_close_cover(self, **kwargs):
        """Open the cover."""
        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0] = 0x01
        packet_data[1] = 0x02
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x01,
            "LOCATION": bytearray(bytes.fromhex(self._id)),
            "DATA": packet_data
        })
        self._state = True
        self.schedule_update_ha_state()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0] = 0x01
        packet_data[1] = 0x03
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x01,
            "LOCATION": bytearray(bytes.fromhex(self._id)),
            "DATA": packet_data
        })
        self._state = not self._state
        self.schedule_update_ha_state()

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        with open("/config/custom_components/xteng_gateway/log.txt", "+a", encoding="utf-8") as file:
            file.write("set: " + str(kwargs))
        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0] = 0x02
        packet_data[1] = 0x04
        packet_data[2] = kwargs['position']
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0xB1,
            "ORDER": 0x01,
            "LOCATION": bytearray(bytes.fromhex(self._id)),
            "DATA": packet_data
        })
