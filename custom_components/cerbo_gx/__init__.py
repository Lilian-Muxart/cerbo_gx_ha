import logging
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components import mqtt
from .mqtt_client import CerboMQTTClient

DOMAIN = "cerbo_gx"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configurer l'intégration Cerbo GX."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurer une entrée de configuration pour Cerbo GX."""
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Récupérer les informations de configuration
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]
    username = entry.data["username"]
    password = entry.data["password"]

    # Initialiser la session HTTP pour la récupération du serveur MQTT
    session = async_get_clientsession(hass)

    # Initialisation du client MQTT avec les données de configuration
    mqtt_client = CerboMQTTClient(
        device_name=device_name,
        id_site=id_site,
        username=username,
        password=password,
        session=session
    )
    
    try:
        # Connexion au serveur MQTT
        await mqtt_client.connect()
        _LOGGER.info("Connexion au serveur MQTT réussie pour %s", device_name)
    except Exception as e:
        _LOGGER.error("Échec de la connexion au serveur MQTT: %s", str(e))
        return False

    # Créer les capteurs dynamiquement pour chaque topic MQTT
    sensor_configs = [
        {
            "state_topic": f"N/{id_site}/system/0/Batteries",
            "name": f"{device_name} Battery Percent",
            "unique_id": f"{device_name}_battery_percent",
            "device_class": "battery",
            "value_template": "{{ value_json.value[0].soc | round(0) }}",
            "unit_of_measurement": "%"
        },
        {
            "state_topic": f"N/{id_site}/system/0/Voltage",
            "name": f"{device_name} Voltage",
            "unique_id": f"{device_name}_voltage",
            "device_class": "voltage",
            "value_template": "{{ value_json.value[0].voltage | round(2) }}",
            "unit_of_measurement": "V"
        },
        {
            "state_topic": f"N/{id_site}/system/0/Temperature",
            "name": f"{device_name} Temperature",
            "unique_id": f"{device_name}_temperature",
            "device_class": "temperature",
            "value_template": "{{ value_json.value[0].temperature | round(1) }}",
            "unit_of_measurement": "°C"
        },
    ]

    # Fonction pour envoyer périodiquement des messages MQTT
    async def publish_data_periodically():
        while True:
            for sensor_config in sensor_configs:
                # Exemple de publication d'un message vide ou d'une valeur périodique
                topic = sensor_config["state_topic"]
                payload = ""  # Envoi d'une valeur vide, ou de données périodiques si nécessaire
                _LOGGER.debug("Publication du message MQTT sur le topic %s", topic)
                mqtt_client.client.publish(topic, payload)

            # Envoi d'un "ping" sur le topic R/[site_id]/system/0/Serial toutes les 30 secondes
            ping_topic = f"R/{id_site}/system/0/Serial"
            ping_payload = ""  # Peut être remplacé par des données pertinentes si nécessaire
            _LOGGER.debug("Envoi du ping sur le topic %s", ping_topic)
            mqtt_client.client.publish(ping_topic, ping_payload)

            # Attente de 30 secondes avant la prochaine publication
            await asyncio.sleep(30)

    # Démarrer la publication périodique dans un thread séparé
    hass.async_create_task(publish_data_periodically())

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger une entrée de configuration."""
    if entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]
    return True
