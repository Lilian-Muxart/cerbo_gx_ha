import logging
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import Platform
from .mqtt_client import CerboMQTTClient

DOMAIN = "cerbo_gx"
PLATFORMS = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configurer l'intégration Cerbo GX."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurer une entrée de configuration pour Cerbo GX."""
    hass.data[DOMAIN][entry.entry_id] = {}

    # Récupérer les informations de configuration
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]
    username = entry.data["username"]
    password = entry.data["password"]

    # Initialisation du client MQTT avec les données de configuration
    mqtt_client = CerboMQTTClient(
        id_site=id_site,
        username=username,
        password=password,
    )

    try:
        # Connexion au serveur MQTT
        await mqtt_client.connect()
        _LOGGER.info("Connexion au serveur MQTT réussie pour %s", device_name)
    except Exception as e:
        _LOGGER.error("Échec de la connexion au serveur MQTT: %s", str(e))
        return False

    # Stocker le client MQTT dans l'intégration
    hass.data[DOMAIN][entry.entry_id]["mqtt_client"] = mqtt_client

    # Configurer les entités associées via la plateforme "sensor"
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger une entrée de configuration."""
    # Décharger les plateformes associées (e.g., sensors)
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Déconnexion et nettoyage
    if entry.entry_id in hass.data[DOMAIN]:
        mqtt_client = hass.data[DOMAIN][entry.entry_id].get("mqtt_client")
        if mqtt_client:
            await mqtt_client.disconnect()
        del hass.data[DOMAIN][entry.entry_id]

    return True

async def get_area_id_by_name(hass: HomeAssistant, room_name: str) -> str:
    """Obtenez l'ID de la pièce à partir de son nom."""
    area_registry = await hass.helpers.entity_registry.async_get_registry()
    for area in area_registry.areas:
        if area.name.lower() == room_name.lower():
            return area.id
    return None