import paho.mqtt.client as mqtt
import ssl
import os
import asyncio
import logging
import json

_LOGGER = logging.getLogger(__name__)

class CerboMQTTClient:
    def __init__(self, id_site, client_id=None, username=None, password=None):
        self.id_site = id_site
        self.client = mqtt.Client(client_id)
        self.username = username
        self.password = password
        self.broker_url = self._get_vrm_broker_url()

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        self.ca_cert_path = os.path.join(os.path.dirname(__file__), "venus-ca.crt")
        if os.path.exists(self.ca_cert_path):
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self._configure_tls)
        else:
            raise FileNotFoundError(f"Le certificat CA n'a pas été trouvé à l'emplacement : {self.ca_cert_path}")
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self._on_global_message
        self.subscriptions = {}  # Dictionnaire pour gérer les abonnements par topic

    def _configure_tls(self):
        """Configure TLS pour la connexion MQTT."""
        self.client.tls_set(ca_certs=self.ca_cert_path, certfile=None, keyfile=None, tls_version=ssl.PROTOCOL_TLSv1_2)

    def _get_vrm_broker_url(self):
        """Générer l'URL du courtier MQTT basé sur l'ID du site."""
        sum = 0
        for character in self.id_site.lower().strip():
            sum += ord(character)
        broker_index = sum % 128
        return f"mqtt{broker_index}.victronenergy.com"

    def connect(self):
        """Connexion au broker MQTT avec démarrage de la boucle de gestion des événements."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._connect_sync)
        loop.create_task(self._keep_alive())

    def _connect_sync(self):
        """Connexion synchronisée au broker MQTT."""
        try:
            self.client.connect(self.broker_url, 8883)
            self.client.loop_start()  # Chaque client a sa propre boucle
        except Exception as e:
            _LOGGER.error(f"Erreur lors de la connexion au serveur MQTT : {e}")

    def disconnect(self):
        """Déconnexion du serveur MQTT."""
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._disconnect_sync)

    def _disconnect_sync(self):
        """Déconnexion synchronisée du serveur MQTT."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            _LOGGER.error(f"Erreur lors de la déconnexion : {e}")

    def on_connect(self, client, userdata, flags, rc):
        """Gestion de l'événement de connexion au broker MQTT."""
        if rc == 0:
            _LOGGER.info(f"Connexion réussie avec le code de retour {rc}")
            keepalive_topic = f"R/{self.id_site}/keepalive"
            self.client.publish(keepalive_topic, "", qos=0)
            _LOGGER.info(f"Message envoyé au topic {keepalive_topic} : ''")

            # Réabonner tous les topics
            for topic in self.subscriptions.keys():
                self.client.subscribe(topic)
                _LOGGER.info(f"Réabonnement au topic : {topic}")
        else:
            _LOGGER.error(f"Erreur de connexion avec le code de retour {rc}")

    def _on_global_message(self, client, userdata, msg):
        """Gestionnaire global pour tous les messages reçus."""
        _LOGGER.debug("Message reçu sur le topic %s : %s", msg.topic, msg.payload)
        if msg.topic in self.subscriptions:
            for callback in self.subscriptions[msg.topic]:
                callback(client, userdata, msg)

    def add_subscription(self, topic, callback):
        """Ajoute un abonnement MQTT avec un callback."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
            self.client.subscribe(topic)  # Souscrire une seule fois par topic
            _LOGGER.debug(f"Souscription ajoutée au topic : {topic}")

        self.subscriptions[topic].append(callback)
        self.client.message_callback_add(topic, self._on_global_message)

    def remove_subscription(self, topic, callback):
        """Supprime un abonnement MQTT et son callback."""
        if topic in self.subscriptions:
            try:
                self.subscriptions[topic].remove(callback)
                _LOGGER.debug(f"Callback supprimé pour le topic : {topic}")

                if not self.subscriptions[topic]:  # Si plus aucun callback pour ce topic
                    del self.subscriptions[topic]
                    self.client.unsubscribe(topic)  # Désinscrire du topic
                    _LOGGER.debug(f"Souscription supprimée pour le topic : {topic}")

            except ValueError:
                _LOGGER.error(f"Callback non trouvé pour le topic : {topic}")

    async def _keep_alive(self):
        """Envoie régulièrement des messages de keep-alive."""
        while True:
            await asyncio.sleep(30)
            keepalive_topic = f"R/{self.id_site}/keepalive"
            self.client.publish(keepalive_topic, "", qos=0)
            _LOGGER.info(f"Message de keep-alive envoyé au topic {keepalive_topic} : ''")

    def publish(self, topic, payload, qos=0, retain=False):
        """Publier un message sur un topic donné."""
        try:
            self.client.publish(topic, payload, qos=qos, retain=retain)
            _LOGGER.info(f"Message publié sur le topic {topic} : {payload}")
        except Exception as e:
            _LOGGER.error(f"Erreur lors de la publication sur le topic {topic}: {e}")


class MQTTManager:
    def __init__(self):
        self.clients = {}

    def add_device(self, id_site, client_id=None, username=None, password=None):
        """Ajoute un client MQTT pour un périphérique avec un ID unique."""
        if id_site in self.clients:
            _LOGGER.warning(f"Le client MQTT pour le site {id_site} existe déjà. Suppression et recréation.")
            self.remove_device(id_site)  # Supprimer l'ancien client avant de le recréer

        # Créer un nouveau client
        self.clients[id_site] = CerboMQTTClient(
            id_site=id_site,
            client_id=client_id,
            username=username,
            password=password,
        )
        self.clients[id_site].connect()
        _LOGGER.info(f"Client MQTT ajouté pour le site {id_site}")

    def get_client(self, id_site):
        """Récupère un client MQTT pour un site donné."""
        return self.clients.get(id_site)

    def remove_device(self, id_site):
        """Supprime un client MQTT pour un périphérique donné."""
        if id_site in self.clients:
            _LOGGER.info(f"Suppression du client MQTT pour le site {id_site}")
            self.clients[id_site].disconnect()
            del self.clients[id_site]
        else:
            _LOGGER.warning(f"Le client MQTT pour le site {id_site} n'existe pas.")
