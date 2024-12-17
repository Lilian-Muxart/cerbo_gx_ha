import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform
from .mqtt_client import CerboMQTTClient
from .sensor import CerboBatterySensor, CerboVoltageSensor, CerboTemperatureSensor

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
        mqtt_client.connect()
        _LOGGER.info("Connexion au serveur MQTT réussie pour %s", device_name)
    except Exception as e:
        _LOGGER.error("Échec de la connexion au serveur MQTT: %s", str(e))
        return False

    # Stocker le client MQTT dans l'intégration
    hass.data[DOMAIN][entry.entry_id]["mqtt_client"] = mqtt_client

    # Configurer les capteurs
    cerbo_battery = CerboBatterySensor(device_name, id_site, mqtt_client)
    cerbo_voltage = CerboVoltageSensor(device_name, id_site, mqtt_client)
    cerbo_temperature = CerboTemperatureSensor(device_name, id_site, mqtt_client)

    # Enregistrer les capteurs dans Home Assistant
    hass.data[DOMAIN][entry.entry_id]["sensors"] = [cerbo_battery, cerbo_voltage, cerbo_temperature]

    # Enregistrer les capteurs dans la plateforme Home Assistant
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger une entrée de configuration."""
    # Décharger les capteurs et autres plateformes
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Déconnexion du client MQTT
    if entry.entry_id in hass.data[DOMAIN]:
        mqtt_client = hass.data[DOMAIN][entry.entry_id].get("mqtt_client")
        if mqtt_client:
            mqtt_client.disconnect()
        del hass.data[DOMAIN][entry.entry_id]

    return True
