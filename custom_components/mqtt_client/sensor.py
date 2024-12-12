""" Implements the VersatileThermostat sensors component """
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,  # pylint: disable=unused-argument
):
    """Configuration de la plate-forme tuto_hacs à partir de la configuration
    trouvée dans configuration.yaml"""

    _LOGGER.debug("Calling async_setup_entry entry=%s", entry)

    entity = TutoHacsElapsedSecondEntity(hass, entry)
    async_add_entities([entity], True)


class TutoHacsElapsedSecondEntity(SensorEntity):
    """La classe de l'entité TutoHacs"""

    def __init__(
        self,
        hass: HomeAssistant,  # pylint: disable=unused-argument
        entry_infos,  # pylint: disable=unused-argument
    ) -> None:
        """Initisalisation de notre entité"""
        self._attr_name = entry_infos.get("name")
        self._attr_unique_id = entry_infos.get("entity_id")
        self._attr_has_entity_name = True