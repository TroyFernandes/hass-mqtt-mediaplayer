""" mqtt-mediaplayer """
from datetime import timedelta
import logging
import homeassistant.loader as loader
import hashlib
import voluptuous as vol
import base64
from homeassistant.helpers.script import Script
from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.const import (
    CONF_NAME,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
)
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ["mqtt"]

_LOGGER = logging.getLogger(__name__)

# TOPICS
TOPICS = "topic"
SONGTITLE_T = "song_title"
SONGARTIST_T = "song_artist"
SONGALBUM_T = "song_album"
SONGVOL_T = "song_volume"
ALBUMART_T = "album_art"
PLAYERSTATUS_T = "player_status"

# END of TOPICS

NEXT_ACTION = "next"
PREVIOUS_ACTION = "previous"
PLAY_ACTION = "play"
PAUSE_ACTION = "pause"
VOLUME_ACTION = "volume"

SUPPORT_MQTTMEDIAPLAYER = (
    SUPPORT_PAUSE
    | SUPPORT_VOLUME_STEP
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_VOLUME_SET
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PLAY
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(TOPICS):
            vol.All({
                vol.Optional(SONGTITLE_T): cv.string,
                vol.Optional(SONGARTIST_T): cv.string,
                vol.Optional(SONGALBUM_T): cv.string,
                vol.Optional(SONGVOL_T): cv.string,
                vol.Optional(ALBUMART_T): cv.string,
                vol.Optional(PLAYERSTATUS_T): cv.string,
            }),
        vol.Optional(NEXT_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PREVIOUS_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PLAY_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PAUSE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(VOLUME_ACTION): cv.SCRIPT_SCHEMA,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MQTT Media Player platform."""

    mqtt = hass.components.mqtt

    topics = config.get("topic")
    for key, value in topics.items():
        if key == "song_title":
            mqtt.subscribe(value, MQTTMediaPlayer.tracktitle_listener)

        if key == "song_artist":
            mqtt.subscribe(value, MQTTMediaPlayer.artist_listener)

        if key == "song_album":
            mqtt.subscribe(value, MQTTMediaPlayer.album_listener)

        if key == "song_volume":
            mqtt.subscribe(value, MQTTMediaPlayer.volume_listener)

        if key == "album_art":
            mqtt.subscribe(value, MQTTMediaPlayer.albumart_listener)

        if key == "player_status":
            mqtt.subscribe(value, MQTTMediaPlayer.state_listener)
    
    entity_name = config.get(CONF_NAME)

    next_action = config.get(NEXT_ACTION)
    previous_action = config.get(PREVIOUS_ACTION)
    play_action = config.get(PLAY_ACTION)
    pause_action = config.get(PAUSE_ACTION) 
    volume_action = config.get(VOLUME_ACTION)

    add_entities([MQTTMediaPlayer(
        entity_name, next_action, previous_action, play_action, pause_action, volume_action, mqtt, hass
        )], )




class MQTTMediaPlayer(MediaPlayerEntity):

    """MQTTMediaPlayer"""

    songTitle = ""
    songArtist = ""
    songAlbum = ""
    songVolume = 0.0
    songAlbumArt = None
    playerState = "paused"
    Self = None

    def __init__(self, name, next_action, previous_action, play_action, pause_action, volume_action, mqtt, hass):
        """Initialize"""
        self._name = name
        self._muted = False
        self._volume = 0.0
        self._track_id = 0
        self._track_name = ""
        self._track_artist = ""
        self._track_album_name = ""
        self._state = None
        self._next_script = Script(hass, next_action)
        self._previous_script = Script(hass, previous_action)
        self._play_script = Script(hass, play_action)
        self._pause_script = Script(hass, pause_action)
        self._volume_script = Script(hass, volume_action)
        self._mqtt = mqtt
        MQTTMediaPlayer.Self = self

    def tracktitle_listener(msg):
        """Handle new MQTT Messages"""
        MQTTMediaPlayer.songTitle = str(msg.payload)
        MQTTMediaPlayer.Self.schedule_update_ha_state(True)

    def artist_listener(msg):
        """Handle new MQTT Messages"""
        MQTTMediaPlayer.songArtist = str(msg.payload)

    def album_listener(msg):
        """Handle new MQTT Messages"""
        MQTTMediaPlayer.songAlbum = str(msg.payload)

    def volume_listener(msg):
        """Handle new MQTT Messages"""
        MQTTMediaPlayer.songVolume = int(msg.payload)
        MQTTMediaPlayer.Self.schedule_update_ha_state(True)

    def albumart_listener(msg):
        """Handle new MQTT Messages"""
        MQTTMediaPlayer.songAlbumArt  = base64.b64decode(msg.payload.replace("\n",""))

    def state_listener(msg):
        """Handle new MQTT Messages"""
        MQTTMediaPlayer.playerState  = str(msg.payload)
        MQTTMediaPlayer.Self.schedule_update_ha_state(True)
    

    def update(self):
        """ Update the States"""

        if MQTTMediaPlayer.playerState == "true":
            self._state = STATE_PLAYING
        else:
            self._state = STATE_PAUSED


        self._track_name = MQTTMediaPlayer.songTitle
        self._track_artist = MQTTMediaPlayer.songArtist
        self._track_album_name = MQTTMediaPlayer.songAlbum
        self._volume = MQTTMediaPlayer.songVolume

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume / 100.0

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    @property
    def media_title(self):
        """Title of current playing media."""
        return self._track_name

    @property
    def media_artist(self):
        """Artist of current playing media, music track only."""
        return self._track_artist

    @property
    def media_album_name(self):
        """Album name of current playing media, music track only."""
        return self._track_album_name

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_MQTTMEDIAPLAYER

    @property
    def media_image_hash(self):
        """Hash value for media image."""
        if MQTTMediaPlayer.songAlbumArt:
            return hashlib.md5(MQTTMediaPlayer.songAlbumArt).hexdigest()[:5]       
        return None

    async def async_get_media_image(self):
        """Fetch media image of current playing image."""
        if MQTTMediaPlayer.songAlbumArt:
            return (MQTTMediaPlayer.songAlbumArt, "image/jpeg")
        return None, None

    def volume_up(self):
        """Volume up the media player."""
        newvolume = min(MQTTMediaPlayer.songVolume + 5, 100)
        MQTTMediaPlayer.songVolume = newvolume
        _LOGGER.debug("Volume_up: " + str(newvolume))
        self.set_volume_level(newvolume)
        self.schedule_update_ha_state(True)

    def volume_down(self):
        """Volume down media player."""
        newvolume = max(MQTTMediaPlayer.songVolume - 5, 0)
        MQTTMediaPlayer.songVolume = newvolume
        _LOGGER.debug("Volume_Down: " + str(newvolume)) 
        self.set_volume_level(newvolume)
        self.schedule_update_ha_state(True)

    def mute_volume(self, mute):
        """Send mute command."""
        _LOGGER.debug("Volume_Down: " + str(mute))
        self.set_volume_level(0)
        self.schedule_update_ha_state(True)

    def set_volume_level(self, volume):
        """Set volume level."""
        self._mqtt.publish("musicbee/command", r'{"command":"volume_set", "args":{"volume":"' + str(volume) + r'"}}' )
        MQTTMediaPlayer.songVolume = volume
        self.schedule_update_ha_state(True)

    async def media_play_pause(self):
        """Simulate play pause media player."""
        if self._state == STATE_PLAYING:
            await self.media_pause()
        else:
            await self.media_play()

    async def media_play(self):
        """Send play command."""
        await self._play_script.async_run(context=self._context)
        self._state = STATE_PLAYING

    async def media_pause(self):
        """Send media pause command to media player."""
        await self._pause_script.async_run(context=self._context)
        self._state = STATE_PAUSED

    async def media_next_track(self):
        """Send next track command."""
        await self._next_script.async_run(context=self._context)

    async def media_previous_track(self):
        """Send the previous track command."""
        await self._previous_script.async_run(context=self._context)
