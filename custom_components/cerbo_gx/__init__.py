from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components import mqtt

DOMAIN = "cerbo_gx"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configurer l'intégration Cerbo GX."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurer une entrée de configuration pour Cerbo GX."""
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Initialiser le client MQTT
    session = async_get_clientsession(hass)
    from .mqtt_client import CerboMQTTClient
    mqtt_client = CerboMQTTClient(entry.data, session)
    await mqtt_client.connect()

    # Créer les capteurs dynamiquement
    device_name = entry.data["device_name"]
    id_site = entry.data["cerbo_id"]

    sensor_configs = [
        {
            "state_topic": f"N/{id_site}/system/0/Batteries",
            "name": f"{device_name} Battery Percent",
            "unique_id": f"{device_name}_battery_percent",
            "device_class": "battery",
            "value_template": "{{ value_json.value[0].soc | round(0) }}",
            "unit_of_measurement": "%"
        },
        # Ajouter d'autres capteurs ici
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
        # Ajoutez ici d'autres capteurs nécessaires
    ]

    # Abonnez-vous aux topics MQTT et créez les capteurs dans Home Assistant
    for sensor_config in sensor_configs:
        async def message_received(msg):
            """Callback pour traiter les messages MQTT."""
            payload = msg.payload.decode("utf-8")
            hass.states.async_set(
                f"sensor.{sensor_config['unique_id']}",
                payload,
                {
                    "name": sensor_config["name"],
                    "unit_of_measurement": sensor_config["unit_of_measurement"],
                    "device_class": sensor_config.get("device_class"),
                    "icon": sensor_config.get("icon"),
                },
            )

        # Souscrire au topic MQTT pour chaque capteur
        hass.components.mqtt.async_subscribe(
            sensor_config["state_topic"], message_received
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger une entrée de configuration."""
    if entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]
    return True
