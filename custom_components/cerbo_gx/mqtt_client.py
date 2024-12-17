import paho.mqtt.client as mqtt
import ssl
import os
import asyncio
import json
import logging

_LOGGER = logging.getLogger(__name__)


class CerboMQTTClient:
    def __init__(self, id_site, client_id=None, username=None, password=None):
        """Initialisation du client MQTT."""
        self.id_site = id_site
        self.client = mqtt.Client(client_id)
        self.username = username
        self.password = password
        self.subscribers = {}  # Dictionnaire pour gérer les abonnés par topic

        # Calculer l'URL du broker basé sur l'ID du site
        self.broker_url = self._get_vrm_broker_url()

        # Configuration de l'authentification MQTT (si les informations sont disponibles)
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # Spécification du chemin du certificat CA par défaut
        self.ca_cert_path = os.path.join(os.path.dirname(__file__), "venus-ca.crt")

        # Vérification de l'existence du certificat
        if os.path.exists(self.ca_cert_path):
            self._configure_tls()
        else:
            raise FileNotFoundError(f"Le certificat CA n'a pas été trouvé à l'emplacement : {self.ca_cert_path}")

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _configure_tls(self):
        """Configurer la connexion sécurisée."""
        self.client.tls_set(
            ca_certs=self.ca_cert_path,
            certfile=None,
            keyfile=None,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )

    def _get_vrm_broker_url(self):
        """Calculer l'URL du serveur MQTT basé sur l'ID du site."""
        sum_ = sum(ord(char) for char in self.id_site.lower().strip())
        broker_index = sum_ % 128
        return f"mqtt{broker_index}.victronenergy.com"

    def connect(self):
        """Connexion au broker MQTT."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._connect_sync)

    def _connect_sync(self):
        """Connexion synchrone au broker MQTT (exécutée dans un thread séparé)."""
        self.client.connect(self.broker_url, 8883)
        self.client.loop_start()  # Lance la boucle dans un thread séparé

    def disconnect(self):
        """Déconnexion et arrêt de la boucle."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._disconnect_sync)

    def _disconnect_sync(self):
        """Déconnexion synchrone du broker MQTT."""
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        """Callback lorsque la connexion au broker MQTT est réussie."""
        if rc == 0:
            _LOGGER.info("Connexion réussie au broker MQTT.")
        else:
            _LOGGER.error(f"Échec de la connexion au broker MQTT, code de retour : {rc}")

    def _on_message(self, client, userdata, msg):
        """Callback pour gérer les messages MQTT."""
        try:
            payload = json.loads(msg.payload)
            _LOGGER.info("Message reçu sur %s: %s", msg.topic, json.dumps(payload, indent=2))
            if msg.topic in self.subscribers:
                for subscriber in self.subscribers[msg.topic]:
                    subscriber.handle_message(payload)
        except Exception as e:
            _LOGGER.error("Erreur de traitement du message MQTT sur %s: %s", msg.topic, e)

    def add_subscriber(self, topic, subscriber):
        """Ajouter un abonné à un topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
            self.client.subscribe(topic)
        self.subscribers[topic].append(subscriber)
