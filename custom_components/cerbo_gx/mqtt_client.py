import paho.mqtt.client as mqtt
import ssl
import os
import asyncio
import logging
import json

_LOGGER = logging.getLogger(__name__)


class CerboMQTTClient:
    def __init__(self, id_site, client_id=None, username=None, password=None):
        """Initialisation du client MQTT."""
        self.id_site = id_site
        self.client = mqtt.Client(client_id)
        self.username = username
        self.password = password
        
        # Calculer l'URL du broker basé sur l'ID du site
        self.broker_url = self._get_vrm_broker_url()

        # Configuration de l'authentification MQTT (si les informations sont disponibles)
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # Spécification du chemin du certificat CA par défaut
        self.ca_cert_path = os.path.join(os.path.dirname(__file__), "venus-ca.crt")
        
        # Vérification de l'existence du certificat
        if os.path.exists(self.ca_cert_path):
            # Assurez-vous que tls_set est exécuté dans un thread séparé pour ne pas bloquer Home Assistant
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self._configure_tls)
        else:
            raise FileNotFoundError(f"Le certificat CA n'a pas été trouvé à l'emplacement : {self.ca_cert_path}")
        self.client.on_connect = self.on_connect

    def _configure_tls(self):
        """Configurer la connexion sécurisée dans un thread séparé."""
        self.client.tls_set(ca_certs=self.ca_cert_path, certfile=None, keyfile=None, tls_version=ssl.PROTOCOL_TLSv1_2)

    def _get_vrm_broker_url(self):
        """Calculer l'URL du serveur MQTT basé sur l'ID du site."""
        sum = 0
        for character in self.id_site.lower().strip():
            sum += ord(character)
        broker_index = sum % 128
        return f"mqtt{broker_index}.victronenergy.com"

    def connect(self):
        """Connexion au broker MQTT (asynchrone)."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._connect_sync)

    def _connect_sync(self):
        """Connexion synchrone au broker MQTT (exécutée dans un thread séparé)."""
        self.client.connect(self.broker_url, 8883)
        self.client.loop_start()  # Lance la boucle dans un thread séparé pour ne pas bloquer

    def disconnect(self):
        """Déconnexion et arrêt de la boucle."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._disconnect_sync)

    def _disconnect_sync(self):
        """Déconnexion synchrone du broker MQTT."""
        self.client.loop_stop()  # Arrêter la boucle
        self.client.disconnect()
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback lorsque la connexion au broker MQTT est réussie."""
        if rc == 0:  # Vérifier que la connexion est réussie
            _LOGGER.info(f"Connexion réussie avec le code de retour {rc}")
            # Envoi du message de keepalive après connexion
            keepalive_topic = f"R/{self.id_site}/keepalive"
            self.client.publish(keepalive_topic, "", qos=0)
            _LOGGER.info(f"Message envoyé au topic {keepalive_topic} : ''")
        else:
            _LOGGER.error(f"Erreur de connexion avec le code de retour {rc}")


    def on_message(self, client, userdata, msg):
        """Callback global pour recevoir tous les messages MQTT."""
        _LOGGER.debug("Message reçu sur le topic %s : %s", msg.topic, msg.payload)
        try:
            payload = json.loads(msg.payload)
            _LOGGER.info("Payload décodé : %s", json.dumps(payload, indent=2))
        except json.JSONDecodeError:
            _LOGGER.error("Erreur de décodage du message JSON sur le topic %s", msg.topic)
            
    def add_subscriber(self, subscriber):
        """Ajouter un abonné pour recevoir les messages MQTT."""
        topic = subscriber.get_state_topic()
        callback = subscriber.on_mqtt_message

        # Log des informations importantes
        _LOGGER.debug("Ajout d'un abonné : topic=%s, callback=%s", topic, callback)

        # Ajout du callback pour le topic
        self.client.message_callback_add(topic, callback)


    def subscribe(self, topic):
        """Souscrire à un topic MQTT."""
        _LOGGER.debug("Souscription au topic : %s", topic)
        result, mid = self.client.subscribe(topic)
        if result == mqtt.MQTT_ERR_SUCCESS:
            _LOGGER.info("Souscription réussie au topic : %s (MID: %s)", topic, mid)
        else:
            _LOGGER.error("Échec de la souscription au topic : %s (Code d'erreur : %s)", topic, result)
