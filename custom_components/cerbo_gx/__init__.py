import logging
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components import mqtt
from homeassistant.const import Platform
from .mqtt_client import CerboMQTTClient
from homeassistant.helpers import entity_registry as er  # Nouveau module pour le registre des entités

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
    room_name = entry.data.get("room_name", "")  # Optionnel : association à une pièce

    # Initialiser la session HTTP pour la récupération du serveur MQTT
    session = async_get_clientsession(hass)

    # Initialisation du client MQTT avec les données de configuration
    mqtt_client = CerboMQTTClient(
        device_name=device_name,
        id_site=id_site,
        username=username,
        password=password,
        session=session,
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

    # Associer l'appareil à une pièce si elle est spécifiée
    if room_name:
        entity_registry = er.async_get(hass)  # Mise à jour pour le registre des entités
        # Assurez-vous que l'ID de l'entité est bien formé
        device_entity_id = f"{DOMAIN}.{device_name.lower()}_sensor"
        _LOGGER.info("Association de l'appareil '%s' à la pièce '%s'", device_entity_id, room_name)
        entity_registry.async_update_entity(
            device_entity_id,
            area_id=room_name,
        )

    # Configurer les entités associées via la plateforme "sensor"
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Lancer une tâche d'envoi périodique de données si nécessaire
    hass.async_create_task(publish_data_periodically(mqtt_client, id_site))

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

async def publish_data_periodically(mqtt_client, id_site: str):
    """Publier périodiquement des messages sur le serveur MQTT."""
    while True:
        try:
            # Envoyer un ping ou autres données si nécessaire
            ping_topic = f"R/{id_site}/system/0/Serial"
            ping_payload = ""
            _LOGGER.debug("Envoi du ping sur le topic %s", ping_topic)
            mqtt_client.client.publish(ping_topic, ping_payload)

            # Attendre 30 secondes avant le prochain envoi
            await asyncio.sleep(30)

        except Exception as e:
            _LOGGER.error("Erreur lors de la publication des données: %s", str(e))
            await asyncio.sleep(30)
