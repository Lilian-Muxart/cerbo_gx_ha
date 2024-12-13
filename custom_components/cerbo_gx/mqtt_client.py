import paho.mqtt.client as mqtt
import asyncio
import logging
import ssl
import os

_LOGGER = logging.getLogger(__name__)

class CerboMQTTClient:
    def __init__(self, device_name, id_site, username, password, session, sensors):
        self.device_name = device_name
        self.id_site = id_site
        self.username = username
        self.password = password
        self.session = session
        self.sensors = sensors  # Liste des capteurs
        self.client = mqtt.Client(client_id=f"cerbo_{id_site}")
        self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.is_connected = False

    def _get_vrm_broker_url(self):
        """Calculer l'URL du serveur MQTT basé sur l'ID du site."""
        total = sum(ord(character) for character in self.id_site.lower().strip())  # Renommage de 'sum' en 'total'
        broker_index = total % 128  # Utilisation de 'total' au lieu de 'sum'
        return f"mqtt{broker_index}.victronenergy.com"


    async def connect(self):
        """Se connecter au serveur MQTT avec l'URL dynamique et activer TLS sur le port 8883."""
        broker_url = self._get_vrm_broker_url()
        _LOGGER.info("Tentative de connexion sécurisée au serveur MQTT: %s", broker_url)

        # Spécifier le fichier de certificat CA
        ca_cert_path = os.path.join(os.path.dirname(__file__), "venus-ca.crt")

        # Configurer la connexion TLS de manière non-bloquante
        await asyncio.to_thread(self.client.tls_set, ca_certs=ca_cert_path, tls_version=ssl.PROTOCOL_TLSv1_2)

        # Connecter au broker de manière non-bloquante et démarrer la boucle MQTT
        await asyncio.gather(
            asyncio.to_thread(self.client.connect, broker_url, 8883, 60),
            asyncio.to_thread(self.client.loop_start)
        )

        # Vérifier la connexion après un délai court
        await asyncio.sleep(2)
        if not self.is_connected:
            _LOGGER.error("Impossible de se connecter au serveur MQTT.")
            raise ConnectionError("Échec de la connexion au serveur MQTT.")

    async def disconnect(self):
        """Déconnexion propre du serveur MQTT."""
        if self.is_connected:
            _LOGGER.info("Déconnexion propre du serveur MQTT.")
            await asyncio.to_thread(self.client.disconnect)

    def on_connect(self, client, userdata, flags, rc):
        """Gérer la connexion réussie."""
        if rc == 0:
            _LOGGER.info("Connecté au serveur MQTT avec succès.")
            self.is_connected = True
            self.client.subscribe(f"N/{self.id_site}/system/0/#")
        else:
            _LOGGER.error("Erreur de connexion MQTT avec code de retour %d", rc)
            self.is_connected = False

    def on_disconnect(self, client, userdata, rc):
        """Gérer la déconnexion."""
        self.is_connected = False
        if rc != 0:
            _LOGGER.warning("Déconnexion imprévue du serveur MQTT, code %d", rc)

    def on_message(self, client, userdata, msg):
        """Gérer la réception de messages MQTT."""
        _LOGGER.debug(f"Message reçu sur le topic {msg.topic}: {msg.payload.decode()}")
        
        # Diffuser le message aux capteurs en fonction du topic
        if msg.topic.startswith(f"N/{self.id_site}/system/0/"):
            sensor_topic = msg.topic[len(f"N/{self.id_site}/system/0/"):]

            # Mettre à jour l'état du capteur approprié
            for sensor in self.sensors:
                if sensor.is_matching_topic(sensor_topic):
                    sensor.on_message(client, userdata, msg)
                    break

    def set_sensor_state(self, sensor_name, state):
        """Mettre à jour l'état d'un capteur."""
        for sensor in self.sensors:
            if sensor.name == sensor_name:
                sensor.state = state
                _LOGGER.info(f"État du capteur {sensor_name} mis à jour à {state}")
                sensor.schedule_update_ha_state()
                break
