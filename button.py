"""Platform for light integration."""
from __future__ import annotations
import random

from homeassistant.components.button import ButtonEntity

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, PORT, BAUDRATE
seq_num = random.randint(0x0001, 0xFFFF)  # 流水号2

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    scenes = hass.data[DOMAIN]['scenes']
    _scenes = []
    for scene in scenes:
        scene_class = XtButton(scene, hass)
        scene_id = scene['sceneId']
        hass.data[DOMAIN]['xteng_dict'][scene_id] = scene_class
        _scenes.append(scene_class)
    add_entities(_scenes)

class XtButton(ButtonEntity):
    # Implement one of these methods.
    def __init__(self, scene_data, hass):
        self._hass = hass
        self._scene_data = scene_data
        self._name = scene_data['sceneName']
        self._id = scene_data['sceneId']
        self._scene_code = scene_data['sceneNo']
        
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id
    
    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    async def async_press(self) -> None:
        global seq_num
        seq_num = (seq_num + 1) % (0xFFFF + 1)
        _data = self._hass.data[DOMAIN]
        packet_data = bytearray(b'\xF5' * 17)
        packet_data[0] = 0x02
        packet_data[1] = 0x03
        packet_data[2:7] = bytearray(bytes.fromhex(self._scene_code))
        packet_data[-4:-2] = seq_num.to_bytes(2, 'big')
        packet_data[-1] = 0xAA
        _data["send_list"].append({
            "PACKET_ID": 0x81,
            "ORDER": 0x0D,
            "LOCATION": b'\xF5' * 7,
            "DATA": packet_data
        })
        _data["get_buffer"].append(self._scene_code)
    