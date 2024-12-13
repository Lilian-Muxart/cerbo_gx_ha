import paho.mqtt.client as mqtt
import asyncio
import logging
import ssl
import os

_LOGGER = logging.getLogger(__name__)

class CerboMQTTClient:
    def __init__(self, device_name, id_site, username, password, session):
        self.device_name = device_name
        self.id_site = id_site
        self.username = username
        self.password = password
        self.session = session
        self.client = mqtt.Client(client_id=f"cerbo_{id_site}")
        self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.is_connected = False

    def _get_vrm_broker_url(self):
        """Calculer l'URL du serveur MQTT basé sur l'ID du site."""
        sum = 0
        for character in self.id_site.lower().strip():
            sum += ord(character)
        broker_index = sum % 128
        return f"mqtt{broker_index}.victronenergy.com"

    async def connect(self):
        """Se connecter au serveur MQTT avec l'URL dynamique et activer TLS sur le port 8883."""
        broker_url = self._get_vrm_broker_url()
        _LOGGER.info("Tentative de connexion sécurisée au serveur MQTT: %s", broker_url)

        # Spécifier le fichier de certificat CA
        ca_cert_path = os.path.join(os.path.dirname(__file__), "venus-ca.crt")

        # Configurer la connexion TLS de manière non-bloquante
        await asyncio.to_thread(self.client.tls_set, ca_certs=ca_cert_path, tls_version=ssl.PROTOCOL_TLSv1_2)

        # Connecter au broker de manière non-bloquante
        loop = asyncio.get_event_loop()
        await asyncio.to_thread(self.client.connect, broker_url, 8883, 60)

        # Démarrer la boucle MQTT dans un thread séparé
        await asyncio.to_thread(self.client.loop_start)
        
        # Vérifier la connexion
        await asyncio.sleep(2)
        if not self.is_connected:
            _LOGGER.error("Impossible de se connecter au serveur MQTT.")
            raise ConnectionError("Échec de la connexion au serveur MQTT.")

    async def disconnect(self):
        """Déconnexion propre du serveur MQTT."""
        loop = asyncio.get_event_loop()
        await asyncio.to_thread(self.client.disconnect)
        if self.is_connected:
            _LOGGER.info("Déconnexion propre du serveur MQTT.")
            loop = asyncio.get_event_loop()
            await asyncio.to_thread(self.client.disconnect)

    def on_connect(self, client, userdata, flags, rc):
        """Gérer la connexion réussie."""
        if rc == 0:
            _LOGGER.info("Connecté au serveur MQTT avec succès.")
            self.is_connected = True
            # Abonnement à tous les topics nécessaires
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
        _LOGGER.debug("Message reçu sur le topic %s: %s", msg.topic, msg.payload.decode())
        
        # Ajouter ici une logique pour traiter les messages reçus et prendre des actions
        # Par exemple : publier un état ou modifier une entité dans Home Assistant.

    async def publish_data_periodically(self):
        """Publier périodiquement des messages sur le serveur MQTT."""
        while True:
            try:
                # Envoi périodique de données (par exemple, un ping ou d'autres informations)
                ping_topic = f"R/{self.id_site}/system/0/Serial"
                ping_payload = ""
                _LOGGER.debug("Envoi du ping sur le topic %s", ping_topic)
                self.client.publish(ping_topic, ping_payload)

                # Attendre 30 secondes avant le prochain envoi
                await asyncio.sleep(30)

            except Exception as e:
                _LOGGER.error("Erreur lors de la publication des données: %s", str(e))
                await asyncio.sleep(30)
