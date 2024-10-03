import json
import base64
import hashlib
import logging
from homeassistant.util.dt import utcnow
from homeassistant.components import media_source
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    async_process_play_media_url
)
from homeassistant.components.mqtt import (
    async_subscribe,
    async_publish,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup entry point."""
    player = MQTTMediaPlayer(hass, config_entry)
    async_add_entities([player])
    # Subscribe to the config topic to get media player configuration dynamically
    CONFIG_TOPIC = f"homeassistant/media_player/{config_entry.title}/config"
    await async_subscribe(hass, CONFIG_TOPIC, player.handle_config)


class MQTTMediaPlayer(MediaPlayerEntity):
    """Representation of a MQTT Media Player."""
   
    def __init__(self, hass, config_entry):
        """Initialize the MQTT Media Player."""
        self._hass = hass
        self._config_entry = config_entry
        self._name = None
        # self._domain = __name__.split(".")[-2]
        self._state = None
        self._volume = 0.0
        self._media_title = None
        self._media_artist = None
        self._media_album = None
        self._album_art = None
        self._duration = None
        self._position = None
        self._available = None
        self._media_type = "music"
        self._subscribed = []


    async def handle_config(self, message):
        """Handle incoming configuration from MQTT."""
        config = json.loads(message.payload)
        _LOGGER.info(f"Received configuration: {config}")
        self._name = config.get("name")

        # Set the MQTT topics from the configuration
        self._availability_topics = {
            "availability_topic": config.get("availability", {}).get("topic"),
            "available": config.get("availability", {}).get("payload_available", "online"),
            "not_available": config.get("availability", {}).get("payload_not_available", "offline"),
        }
        self._state_topics = {
            "state_topic": config.get("state_state_topic"),
            "title_topic": config.get("state_title_topic"),
            "artist_topic": config.get("state_artist_topic"),
            "album_topic": config.get("state_album_topic"),
            "duration_topic": config.get("state_duration_topic"),
            "position_topic": config.get("state_position_topic"),
            "volume_topic": config.get("state_volume_topic"),
            "albumart_topic": config.get("state_albumart_topic"),
            "mediatype_topic": config.get("state_mediatype_topic"),
        }
        self._cmd_topics = {
            "volumeset_topic": config.get("command_volume_topic"),
            "play_topic": config.get("command_play_topic"),
            "play_payload": config.get("command_play_payload", "Play"),
            "pause_topic": config.get("command_pause_topic"),
            "pause_payload": config.get("command_pause_payload", "Pause"),
            "next_topic": config.get("command_next_topic"),
            "next_payload": config.get("command_next_payload", "Next"),
            "previous_topic": config.get("command_previous_topic"),
            "previous_payload": config.get("command_previous_payload", "Previous"),
            "playmedia_topic": config.get("command_playmedia_topic"),
        }

        # Unsubscribe from subscribed topics
        for subscription in self._subscribed:
            subscription()
        self._subscribed = []

        # Subscribe to relevant state topics
        if (check_topic := self._state_topics["state_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_state))
        if (check_topic := self._state_topics["title_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_title))
        if (check_topic := self._state_topics["artist_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_artist))
        if (check_topic := self._state_topics["album_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_album))
        if (check_topic := self._state_topics["duration_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_duration))
        if (check_topic := self._state_topics["position_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_position))
        if (check_topic := self._state_topics["volume_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_volume))
        if (check_topic := self._state_topics["albumart_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_albumart))
        if (check_topic := self._state_topics["mediatype_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_mediatype))
        if (check_topic := self._availability_topics["availability_topic"]) is not None:
            self._subscribed.append(await async_subscribe(self._hass, check_topic, self.handle_availability))

    @property
    def supported_features(self):
        """Return supported features."""
        return (
            MediaPlayerEntityFeature.PLAY |
            MediaPlayerEntityFeature.PAUSE |
            MediaPlayerEntityFeature.STOP |
            MediaPlayerEntityFeature.VOLUME_SET |
            MediaPlayerEntityFeature.VOLUME_STEP |
            MediaPlayerEntityFeature.NEXT_TRACK |
            MediaPlayerEntityFeature.PREVIOUS_TRACK |
            MediaPlayerEntityFeature.PLAY_MEDIA
        )

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._config_entry.title

    @property
    def state(self):
        if self._available is False:
            return "unavailable"
        return self._state

    @property
    def volume_level(self):
        return self._volume

    @property
    def media_title(self):
        return self._media_title

    @property
    def media_artist(self):
        return self._media_artist

    @property
    def media_album_name(self):
        return self._media_album

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return self._media_type

    @property
    def media_position(self):
        """Position of player in percentage."""
        return self._position

    @property
    def media_duration(self):
        """Duration of current playing media in percentage."""
        return self._duration

    @property
    def media_image_hash(self):
        """Hash value for media image."""
        if self._album_art:
            return hashlib.md5(self._album_art).hexdigest()[:5]       
        return None

    async def async_get_media_image(self):
        """Fetch media image of current playing image."""
        if self._album_art:
            return (self._album_art, "image/jpeg")
        return None, None

    async def handle_availability(self, message):
        """Update the media player availability status."""
        if message.payload == self._availability_topics["available"]:
            self._available = True
        elif message.payload == self._availability_topics["not_available"]:
            self._available = False
        self.async_write_ha_state()

    async def handle_state(self, message):
        """Update the player state based on the MQTT state topic."""
        print("Changed state:", message.payload)
        self._state = message.payload
        self.async_write_ha_state()

    async def handle_title(self, message):
        """Update the media title based on the MQTT title topic."""
        self._media_title = message.payload
        self.async_write_ha_state()

    async def handle_artist(self, message):
        """Update the media artist based on the MQTT artist topic."""
        self._media_artist = message.payload
        self.async_write_ha_state()

    async def handle_album(self, message):
        """Update the media album based on the MQTT album topic."""
        self._media_album = message.payload
        self.async_write_ha_state()

    async def handle_duration(self, message):
        """Update the media duration based on the MQTT duration topic."""
        try:
            self._duration = int(message.payload)
        except:
            self._position = None
        self.async_write_ha_state()

    async def handle_position(self, message):
        """Update the media position based on the MQTT position topic."""
        try:
            self._position = int(message.payload)
            self._attr_media_position_updated_at = utcnow()
        except:
            self._position = None
        self.async_write_ha_state()

    async def handle_volume(self, message):
        """Update the volume based on the MQTT volume topic."""
        self._volume = float(message.payload)
        self.async_write_ha_state()

    async def handle_albumart(self, message):
        """Update the album art based on the MQTT album art topic."""
        self._album_art = base64.b64decode(message.payload.replace("\n",""))
        self.async_write_ha_state()

    async def handle_mediatype(self, message):
        """Update the media media_type based on the MQTT media_type topic."""
        self._media_type = message.payload
        self.async_write_ha_state()

    async def async_media_play(self):
        """Send play command via MQTT."""
        await async_publish(self._hass, self._cmd_topics["play_topic"], self._cmd_topics["play_payload"])

    async def async_media_pause(self):
        """Send pause command via MQTT."""
        await async_publish(self._hass, self._cmd_topics["pause_topic"], self._cmd_topics["pause_payload"])

    async def async_media_next_track(self):
        """Send next track command via MQTT."""
        await async_publish(self._hass, self._cmd_topics["next_topic"], self._cmd_topics["next_payload"])

    async def async_media_previous_track(self):
        """Send previous track command via MQTT."""
        await async_publish(self._hass, self._cmd_topics["previous_topic"], self._cmd_topics["previous_payload"])

    async def async_set_volume_level(self, volume):
        """Set the volume level via MQTT."""
        self._volume = round(float(volume), 2)
        await async_publish(self._hass, self._cmd_topics["volumeset_topic"], self._volume)

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Sends media to play."""
        if media_source.is_media_source_id(media_id):
            sourced_media = await media_source.async_resolve_media(self.hass, media_id)
            media_type = sourced_media.mime_type
            media_id = async_process_play_media_url(self.hass, sourced_media.url)
        media = {
            "media_type": media_type,
            "media_id": media_id,
        }
        await async_publish(self._hass, self._cmd_topics["playmedia_topic"], json.dumps(media))
