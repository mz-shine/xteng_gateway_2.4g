"""Platform for light integration."""
from __future__ import annotations
import random

from homeassistant.components.button import ButtonEntity

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN

seq_num = random.randint(0x0001, 0xFFFF)  # 流水号

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    scenes = hass.data[DOMAIN]['scenes']
    entities = []
    for scene in scenes:
        entity = XtButtonEntity(scene, hass)
        hass.data[DOMAIN]['entities'][entity.unique_id] = entity
        entities.append(entity)
    add_entities(entities)

class XtButtonEntity(ButtonEntity):
    def __init__(self, scene, hass):
        self._hass = hass
        self._scene_data = scene
        self._name = scene['sceneName']
        self._id = scene['sceneId']
        self._scene_code = scene['sceneNo']
        
        self.gateway_id = bytearray(bytes.fromhex(scene['gatewayId']))
        self.location = bytearray(bytes.fromhex(scene['sceneNo']))
        self.packet = self.set_packet()

    def set_packet(self):
        packet = bytearray([0x55, 0x19, 0x0D, 0x00, 0x13, 0x02, 0x01])
        packet.extend(self.location)
        packet.extend(self.gateway_id)
        packet.extend(self.gateway_id[2:])
        packet.extend(seq_num.to_bytes(2, 'big'))
        packet.append(0xAA)
        return packet

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id
    
    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    async def async_press(self) -> None:
        _data = self._hass.data[DOMAIN]
        seq_num = (seq_num + 1) % (0xFFFF + 1)

        self.packet[-3:-1] = seq_num.to_bytes(2, 'big')
        _data["send"].append(self.packet)
        # _data["get_buffer"].append(self._scene_code)
    