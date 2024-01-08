""" mqtt-mediaplayer """
import logging
import homeassistant.loader as loader
import hashlib
import voluptuous as vol
import base64
from homeassistant.exceptions import TemplateError, NoEntitySpecifiedError
from homeassistant.helpers.script import Script
from homeassistant.helpers.event import TrackTemplate, async_track_template_result, async_track_state_change
from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC
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
CURRENT_SOURCE_T = "source"
SOURCE_LIST_T = "source_list"

# END of TOPICS

NEXT_ACTION = "next"
PREVIOUS_ACTION = "previous"
PLAY_ACTION = "play"
PAUSE_ACTION = "pause"
VOL_DOWN_ACTION = "vol_down"
VOL_UP_ACTION = "vol_up"
VOLUME_ACTION = "volume"
PLAYERSTATUS_KEYWORD = "status_keyword"
SELECT_SOURCE_ACTION = "select_source"
TURN_OFF_ACTION = "turn_off"
TURN_ON_ACTION = "turn_on"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(TOPICS):
            vol.All({
                vol.Optional(SONGTITLE_T): cv.template,
                vol.Optional(SONGARTIST_T): cv.template,
                vol.Optional(SONGALBUM_T): cv.template,
                vol.Optional(SONGVOL_T): cv.template,
                vol.Optional(ALBUMART_T): cv.string,
                vol.Optional(PLAYERSTATUS_T): cv.template,
                vol.Optional(CURRENT_SOURCE_T): cv.template,
                vol.Optional(SOURCE_LIST_T, default=[]): vol.All(
                    cv.ensure_list, [{vol.Required("id"): cv.string,
                                      vol.Required("name"): cv.string}]),
                vol.Optional(VOLUME_ACTION): cv.SCRIPT_SCHEMA
            }),
        vol.Optional(NEXT_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PREVIOUS_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PLAY_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PAUSE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(VOL_DOWN_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(VOL_UP_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(TURN_OFF_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(TURN_ON_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(SELECT_SOURCE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PLAYERSTATUS_KEYWORD): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MQTT Media Player platform."""
    mqtt = hass.components.mqtt

    topics = config.get(TOPICS)    
    entity_name = config.get(CONF_NAME)
    next_action = config.get(NEXT_ACTION)
    previous_action = config.get(PREVIOUS_ACTION)
    play_action = config.get(PLAY_ACTION)
    pause_action = config.get(PAUSE_ACTION) 
    vol_down_action = config.get(VOL_DOWN_ACTION)
    vol_up_action = config.get(VOL_UP_ACTION)
    volume_action = config.get(VOLUME_ACTION)
    turn_off_action = config.get(TURN_OFF_ACTION)
    turn_on_action = config.get(TURN_ON_ACTION)
    select_source_action = config.get(SELECT_SOURCE_ACTION)
    player_status_keyword = config.get(PLAYERSTATUS_KEYWORD)


    add_entities([MQTTMediaPlayer(
        entity_name, next_action, previous_action, play_action, pause_action, 
        vol_down_action, vol_up_action, player_status_keyword, 
        topics, mqtt, hass,
        turn_off_action, turn_on_action, select_source_action,
        )], )


class MQTTMediaPlayer(MediaPlayerEntity):
    """MQTTMediaPlayer"""

    def __init__(self, name, next_action, previous_action, play_action, pause_action, 
    vol_down_action, vol_up_action, player_status_keyword, 
    topics, mqtt, hass,
    turn_off_action, turn_on_action, select_source_action):
        """Initialize"""
        self.hass = hass
        self._domain = __name__.split(".")[-2]
        self._name = name
        self._volume = 0.0
        self._track_name = ""
        self._track_artist = ""
        self._track_album_name = ""
        self._mqtt_player_state = None
        self._state = None
        self._album_art = None
        self._next_script = None
        self._previous_script = None
        self._play_script = None
        self._pause_script = None
        self._vol_down_action = None
        self._vol_up_action = None
        self._vol_script = None
        self._select_source_script = None
        self._turn_off_script = None
        self._turn_on_script = None
        self._source = None
        self._source_list = None

        self.SUPPORT_MQTTMEDIAPLAYER = 0

        if(next_action):
            self._next_script = Script(hass, next_action, self._name, self._domain)
            self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.NEXT_TRACK
        if(previous_action):
            self._previous_script = Script(hass, previous_action, self._name, self._domain)
            self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if(play_action):
            self._play_script = Script(hass, play_action, self._name, self._domain)
            self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.PLAY
        if(pause_action):
            self._pause_script = Script(hass, pause_action, self._name, self._domain)
            self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.PAUSE
        if(vol_down_action):
            self._vol_down_action = Script(hass, vol_down_action, self._name, self._domain)
            self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.VOLUME_STEP
        if(vol_up_action):
            self._vol_up_action = Script(hass, vol_up_action, self._name, self._domain)        
        if(select_source_action):
            self._select_source_script = Script(hass, select_source_action, self._name, self._domain)
            self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.SELECT_SOURCE
        if(turn_off_action):
            self._turn_off_script = Script(hass, turn_off_action, self._name, self._domain)
            self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.TURN_OFF
        if(turn_on_action):
            self._turn_on_script = Script(hass, turn_on_action, self._name, self._domain)
            self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.TURN_ON

        self._player_status_keyword = player_status_keyword

        if topics is not None:
            for key, value in topics.items():
                
                if key == "song_title":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.tracktitle_listener)
                    self.async_on_remove(result.async_remove)

                if key == "song_artist":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.artist_listener)
                    self.async_on_remove(result.async_remove)

                if key == "song_album":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.album_listener)
                    self.async_on_remove(result.async_remove)

                if key == "song_volume":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.volume_listener)
                    self.async_on_remove(result.async_remove)

                if key == "album_art":
                    mqtt.subscribe(value, self.albumart_listener)

                if key == "player_status":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.state_listener)
                    self.async_on_remove(result.async_remove)

                if key == "volume":
                    self._vol_script = Script(hass, value, self._name, self._domain)
                    self.SUPPORT_MQTTMEDIAPLAYER |= MediaPlayerEntityFeature.VOLUME_SET

                if key == "source":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.source_listener)
                    self.async_on_remove(result.async_remove)

                if key == "source_list":
                    self._source_list = value

    @property
    def source_list(self):
        return [entry['name'] for entry in self._source_list]

    async def tracktitle_listener(self, event, updates):
        """Listen for the Track Title change"""
        result = updates.pop().result
        self._track_name = result
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def artist_listener(self, event, updates):
        """Listen for the Artis Name change"""
        result = updates.pop().result
        self._track_artist = result

    async def source_list_listener(self, event, updates):
        """Listen for the Source change"""
        result = updates.pop().result
        self._source_list = result

    async def source_listener(self, event, updates):
        """Listen for the Source change"""
        result = updates.pop().result
        for entry in self._source_list:
            if int(entry['id']) == int(result):
                self._source = entry['name']
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def album_listener(self, event, updates):
        """Listen for the Album Name change"""
        result = updates.pop().result
        self._track_album_name = result

    async def volume_listener(self, event, updates):
        """Listen for Player Volume changes"""
        result = updates.pop().result
        _LOGGER.debug("Volume Listener: " + str(result))
        if isinstance(result, int):
            self._volume = int(result)
            if MQTTMediaPlayer:
                self.schedule_update_ha_state(True)

    async def albumart_listener(self, msg):
        """Listen for the Album Art change"""
        self._album_art  = base64.b64decode(msg.payload.replace("\n",""))

    async def state_listener(self, event, updates):
        """Listen for Player State changes"""
        result = updates.pop().result
        self._mqtt_player_state  = str(result)
        self._state  = str(result)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    def update(self):
        """ Update the States"""
        if self._player_status_keyword:
            if self._mqtt_player_state == self._player_status_keyword:
                self._state = STATE_PLAYING
            else:
                self._state = STATE_PAUSED
        else:
            self._state = self._mqtt_player_state

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
        return self.SUPPORT_MQTTMEDIAPLAYER

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

    async def async_volume_up(self):
        """Volume up the media player."""
        if(self._vol_up_action):
            await self._vol_up_action.async_run(context=self._context)
        else:
            newvolume = min(self._volume + 5, 100)
            self._volume = newvolume
            await self.async_set_volume_level(newvolume)

    async def async_volume_down(self):
        """Volume down media player."""
        if(self._vol_down_action):
            await self._vol_down_action.async_run(context=self._context)
        else:
            newvolume = max(self._volume - 5, 0)
            self._volume = newvolume
            await self.async_set_volume_level(newvolume)

    async def async_set_volume_level(self, volume):
        """Set volume level."""
        if(self._vol_down_action or self._vol_down_action):
            return
        if(self._vol_script):
            await self._vol_script.async_run({"volume": volume}, context=self._context)
            self._volume = volume

    async def async_media_play_pause(self):
        """Simulate play pause media player."""
        if self._state == STATE_PLAYING:
            await self.async_media_pause()
        else:
            await self.async_media_play()

    async def async_media_play(self):
        """Send play command."""
        if(self._play_script):
            await self._play_script.async_run(context=self._context)
            self._state = STATE_PLAYING

    async def async_media_pause(self):
        """Send media pause command to media player."""
        if(self._pause_script):
            await self._pause_script.async_run(context=self._context)
            self._state = STATE_PAUSED

    async def async_media_next_track(self):
        """Send next track command."""
        if(self._next_script):
            await self._next_script.async_run(context=self._context)

    async def async_media_previous_track(self):
        """Send the previous track command."""
        if(self._previous_script):
            await self._previous_script.async_run(context=self._context)

    async def async_select_source(self, source):
        """Send source select command."""
        if(self._select_source_script):
            for entry in self._source_list:
                if entry['name'] == source:
                    id_ = entry['id']
            await self._select_source_script.async_run({"source": id_}, context=self._context)
            self._source = source

    async def async_turn_off(self):
        """Send turn off command."""
        if(self._turn_off_script):
            await self._turn_off_script.async_run(context=self._context)

    async def async_turn_on(self):
        """Send turn on command."""
        if(self._turn_on_script):
            await self._turn_on_script.async_run(context=self._context)

    @property
    def source(self):
        return self._source