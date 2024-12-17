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
        
        self.reconnect_interval = 180  # Intervalle de reconnexion en secondes (3 minutes)
        self.reconnect_timer = None  # Timer pour la reconnexion automatique

    def _configure_tls(self):
        self.client.tls_set(ca_certs=self.ca_cert_path, certfile=None, keyfile=None, tls_version=ssl.PROTOCOL_TLSv1_2)

    def _get_vrm_broker_url(self):
        sum = 0
        for character in self.id_site.lower().strip():
            sum += ord(character)
        broker_index = sum % 128
        return f"mqtt{broker_index}.victronenergy.com"

    def connect(self):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._connect_sync)

    def _connect_sync(self):
        self.client.connect(self.broker_url, 8883)
        self.client.loop_start()
        
        # Planifier la reconnexion toutes les 3 minutes
        self._schedule_reconnect()

    def on_connect(self, client, userdata, flags, rc):
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

    def _schedule_reconnect(self):
        """Planifie une reconnexion toutes les 3 minutes."""
        # Utiliser le contexte actuel de boucle d'événements (ici on suppose que c'est déjà le bon thread)
        loop = asyncio.get_running_loop()
        self.reconnect_timer = loop.call_later(self.reconnect_interval, self.reconnect)

    def reconnect(self):
        """Reconnecte le client MQTT."""
        _LOGGER.info("Tentative de reconnexion...")
        self.client.reconnect()
        self._schedule_reconnect()  # Répéter la reconnexion toutes les 3 minutes
