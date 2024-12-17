import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform
from .mqtt_client import MQTTManager

DOMAIN = "cerbo_gx"
PLATFORMS = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)

# Instancier le gestionnaire de clients MQTT
mqtt_manager = MQTTManager()

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

    # Ajouter un client MQTT via le gestionnaire
    try:
        # Ajouter le client avec l'ID du site et les informations de connexion
        mqtt_manager.add_device(id_site, client_id=device_name, username=username, password=password)
        _LOGGER.info("Connexion au serveur MQTT réussie pour %s", device_name)
    except Exception as e:
        _LOGGER.error("Échec de la connexion au serveur MQTT pour %s : %s", device_name, str(e))
        return False

    # Stocker le client MQTT dans l'intégration
    hass.data[DOMAIN][entry.entry_id]["mqtt_client"] = mqtt_manager.get_client(id_site)

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
            # Arrêter la boucle de MQTT et se déconnecter proprement
            mqtt_client.disconnect()
        del hass.data[DOMAIN][entry.entry_id]

    return True

async def get_area_id_by_name(hass: HomeAssistant, room_name: str) -> str:
    """Obtenez l'ID de la pièce à partir de son nom."""
    area_registry = await hass.helpers.entity_registry.async_get_registry()
    for area in area_registry.areas:
        if area.name.lower() == room_name.lower():
            return area.id
    return None
