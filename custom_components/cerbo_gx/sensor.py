from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_platform
from .const import DOMAIN, CONF_DEVICE_NAME, CONF_ROOM

async def async_setup_entry(hass, config_entry, async_add_entities):
    device_name = config_entry.data[CONF_DEVICE_NAME]
    device_room = config_entry.data[CONF_ROOM]
    async_add_entities([MyIntegrationSensor(device_name, device_room)])

class MyIntegrationSensor(SensorEntity):
    def __init__(self, name, room):
        self._attr_name = name
        self._attr_area = room  # Utilise 'area' plutôt que 'room'
        self._state = None

    @property
    def state(self):
        return self._state

    async def async_update(self):
        # Mettre à jour l'état du capteur ici
        self._state = "Example state"
    
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._attr_name)},
            "name": self._attr_name,
        }
