""" mqtt-mediaplayer """
import logging
import json
import homeassistant.loader as loader
import hashlib
import voluptuous as vol
import base64
from homeassistant.exceptions import TemplateError, NoEntitySpecifiedError
from homeassistant.helpers.script import Script
from homeassistant.helpers.event import TrackTemplate, async_track_template_result, async_track_state_change
from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity, MediaPlayerEntityFeature, MediaType, RepeatMode
import homeassistant.components.mqtt as mqtt
from homeassistant.const import (
    CONF_NAME,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_IDLE,
    STATE_BUFFERING,
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
PLAYERSTATE_T = "player_state"
CURRENT_SOURCE_T = "source"
SOURCE_LIST_T = "source_list"
SHUFFLE_T = "shuffle_mode"
REPEAT_T = "repeat_mode"
MUTED_T = "muted"
MEDIA_DURATION_T = "media_duration"
MEDIA_POSITION_T = "media_position"
CONTENT_TYPE_T = "content_type"
TRACK_NUMBER_T = "track_number"
GENRE_T = "genre"
ALBUM_ARTIST_T = "album_artist"
YEAR_T = "year"

# END of TOPICS

NEXT_ACTION = "next"
PREVIOUS_ACTION = "previous"
PLAY_ACTION = "play"
PAUSE_ACTION = "pause"
STOP_ACTION = "stop"
VOL_DOWN_ACTION = "vol_down"
VOL_UP_ACTION = "vol_up"
VOLUME_ACTION = "volume"
PLAYERSTATUS_KEYWORD = "status_keyword"
SELECT_SOURCE_ACTION = "select_source"
TURN_OFF_ACTION = "turn_off"
TURN_ON_ACTION = "turn_on"
SHUFFLE_SET_ACTION = "shuffle_set"
REPEAT_SET_ACTION = "repeat_set"
SEEK_ACTION = "seek"
MUTE_ACTION = "mute"

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
                vol.Optional(PLAYERSTATE_T): cv.template,
                vol.Optional(CURRENT_SOURCE_T): cv.template,
                vol.Optional(SOURCE_LIST_T, default=[]): vol.Any(
                    cv.string,
                    vol.All(
                        cv.ensure_list, [{vol.Required("id"): cv.string,
                                          vol.Required("name"): cv.string}]),
                ),
                vol.Optional(VOLUME_ACTION): cv.SCRIPT_SCHEMA,
                vol.Optional(SHUFFLE_T): cv.template,
                vol.Optional(REPEAT_T): cv.template,
                vol.Optional(MUTED_T): cv.template,
                vol.Optional(MEDIA_DURATION_T): cv.template,
                vol.Optional(MEDIA_POSITION_T): cv.template,
                vol.Optional(CONTENT_TYPE_T): cv.template,
                vol.Optional(TRACK_NUMBER_T): cv.template,
                vol.Optional(GENRE_T): cv.template,
                vol.Optional(ALBUM_ARTIST_T): cv.template,
                vol.Optional(YEAR_T): cv.template,
            }),
        vol.Optional(NEXT_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PREVIOUS_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PLAY_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PAUSE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(STOP_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(VOL_DOWN_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(VOL_UP_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(TURN_OFF_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(TURN_ON_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(SELECT_SOURCE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(SHUFFLE_SET_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(REPEAT_SET_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(SEEK_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(MUTE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(PLAYERSTATUS_KEYWORD): cv.string,
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the MQTT Media Player platform."""

    topics = config.get(TOPICS)    
    entity_name = config.get(CONF_NAME)
    next_action = config.get(NEXT_ACTION)
    previous_action = config.get(PREVIOUS_ACTION)
    play_action = config.get(PLAY_ACTION)
    pause_action = config.get(PAUSE_ACTION)
    stop_action = config.get(STOP_ACTION)
    vol_down_action = config.get(VOL_DOWN_ACTION)
    vol_up_action = config.get(VOL_UP_ACTION)
    volume_action = config.get(VOLUME_ACTION)
    turn_off_action = config.get(TURN_OFF_ACTION)
    turn_on_action = config.get(TURN_ON_ACTION)
    select_source_action = config.get(SELECT_SOURCE_ACTION)
    shuffle_set_action = config.get(SHUFFLE_SET_ACTION)
    repeat_set_action = config.get(REPEAT_SET_ACTION)
    seek_action = config.get(SEEK_ACTION)
    mute_action = config.get(MUTE_ACTION)
    player_status_keyword = config.get(PLAYERSTATUS_KEYWORD)

    entity = MQTTMediaPlayer(
        entity_name, next_action, previous_action, play_action, pause_action,
        stop_action, vol_down_action, vol_up_action, player_status_keyword, 
        turn_off_action, turn_on_action, select_source_action,
        shuffle_set_action, repeat_set_action, seek_action, mute_action,
        topics, hass
    )

    async_add_entities([entity])

    await entity.async_setup()


class MQTTMediaPlayer(MediaPlayerEntity):
    """MQTTMediaPlayer"""

    def __init__(self, name, next_action, previous_action, play_action, pause_action,
                 stop_action, vol_down_action, vol_up_action, player_status_keyword, 
                 turn_off_action, turn_on_action, select_source_action,
                 shuffle_set_action, repeat_set_action, seek_action, mute_action,
                 topics, hass):
        
        """Initialize"""
        self.hass = hass
        self._domain = __name__.split(".")[-2]
        self._name = name
        self._volume = 0.0
        self._track_name = ""
        self._track_artist = ""
        self._track_album_name = ""
        self._track_album_artist = ""
        self._track_genre = ""
        self._track_year = ""
        self._track_number = ""
        self._content_type = MediaType.MUSIC
        self._mqtt_player_state = None
        self._state = None
        self._album_art = None
        self._next_script = None
        self._previous_script = None
        self._play_script = None
        self._pause_script = None
        self._stop_script = None
        self._vol_down_action = None
        self._vol_up_action = None
        self._vol_script = None
        self._select_source_script = None
        self._turn_off_script = None
        self._turn_on_script = None
        self._shuffle_set_script = None
        self._repeat_set_script = None
        self._seek_script = None
        self._mute_script = None
        self._source = None
        self._source_list = None
        self._source_list_names = None
        self._shuffle = False
        self._repeat = RepeatMode.OFF
        self._muted = False
        self._media_duration = None
        self._media_position = None
        self._media_position_updated_at = None

        if next_action:
            self._next_script = Script(hass, next_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.NEXT_TRACK
        if previous_action:
            self._previous_script = Script(hass, previous_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if play_action:
            self._play_script = Script(hass, play_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.PLAY
        if pause_action:
            self._pause_script = Script(hass, pause_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.PAUSE
        if stop_action:
            self._stop_script = Script(hass, stop_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.STOP
        if vol_down_action:
            self._vol_down_action = Script(hass, vol_down_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.VOLUME_STEP
        if vol_up_action:
            self._vol_up_action = Script(hass, vol_up_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.VOLUME_STEP
        if select_source_action:
            self._select_source_script = Script(hass, select_source_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.SELECT_SOURCE
        if turn_off_action:
            self._turn_off_script = Script(hass, turn_off_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.TURN_OFF
        if turn_on_action:
            self._turn_on_script = Script(hass, turn_on_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.TURN_ON
        if shuffle_set_action:
            self._shuffle_set_script = Script(hass, shuffle_set_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.SHUFFLE_SET
        if repeat_set_action:
            self._repeat_set_script = Script(hass, repeat_set_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.REPEAT_SET
        if seek_action:
            self._seek_script = Script(hass, seek_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.SEEK
        if mute_action:
            self._mute_script = Script(hass, mute_action, self._name, self._domain)
            self._attr_supported_features |= MediaPlayerEntityFeature.VOLUME_MUTE
        
        self._player_status_keyword = player_status_keyword
        self._topics = topics

    async def async_setup(self):
        """Set up the MQTT subscriptions."""
        if self._topics is not None:
            for key, value in self._topics.items():
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
                    await mqtt.async_subscribe(self.hass, value, self.albumart_listener)

                if key == "player_status":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.state_listener)
                    self.async_on_remove(result.async_remove)

                if key == "player_state":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.player_state_listener)
                    self.async_on_remove(result.async_remove)

                if key == "volume":
                    self._vol_script = Script(self.hass, value, self._name, self._domain)
                    self._attr_supported_features |= MediaPlayerEntityFeature.VOLUME_SET

                if key == "source":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.source_listener)
                    self.async_on_remove(result.async_remove)

                if key == "source_list":
                    if isinstance(value, str):
                        # MQTT topic - subscribe directly
                        await mqtt.async_subscribe(self.hass, value, self.source_list_mqtt_listener)
                    elif isinstance(value, list):
                        self._source_list = value

                if key == "shuffle_mode":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.shuffle_listener)
                    self.async_on_remove(result.async_remove)

                if key == "repeat_mode":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.repeat_listener)
                    self.async_on_remove(result.async_remove)

                if key == "muted":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.muted_listener)
                    self.async_on_remove(result.async_remove)

                if key == "media_duration":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.duration_listener)
                    self.async_on_remove(result.async_remove)

                if key == "media_position":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.position_listener)
                    self.async_on_remove(result.async_remove)

                if key == "content_type":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.content_type_listener)
                    self.async_on_remove(result.async_remove)

                if key == "track_number":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.track_number_listener)
                    self.async_on_remove(result.async_remove)

                if key == "genre":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.genre_listener)
                    self.async_on_remove(result.async_remove)

                if key == "album_artist":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.album_artist_listener)
                    self.async_on_remove(result.async_remove)

                if key == "year":
                    result = async_track_template_result(self.hass, [TrackTemplate(value, None)], self.year_listener)
                    self.async_on_remove(result.async_remove)


    @property
    def source_list(self):
        if self._source_list_names:
            return self._source_list_names
        if self._source_list is None:
            return []
        return [entry['name'] for entry in self._source_list]

    async def tracktitle_listener(self, event, updates):
        """Listen for the Track Title change"""
        result = updates.pop().result
        self._track_name = result
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def artist_listener(self, event, updates):
        """Listen for the Artist Name change"""
        result = updates.pop().result
        self._track_artist = result
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def source_list_listener(self, event, updates):
        """Listen for the Source change (legacy)"""
        result = updates.pop().result
        self._source_list = result

    async def source_list_mqtt_listener(self, msg):
        """Listen for source list via direct MQTT subscription"""
        try:
            devices = json.loads(msg.payload)
            if isinstance(devices, list):
                self._source_list_names = devices
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def source_listener(self, event, updates):
        """Listen for the Source change"""
        result = updates.pop().result
        if self._source_list:
            # Static list: map ID to name
            for entry in self._source_list:
                if int(entry['id']) == int(result):
                    self._source = entry['name']
        else:
            # Dynamic: use value directly as the source name
            self._source = str(result)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def album_listener(self, event, updates):
        """Listen for the Album Name change"""
        result = updates.pop().result
        self._track_album_name = result
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def volume_listener(self, event, updates):
        """Listen for Player Volume changes"""
        result = updates.pop().result
        _LOGGER.debug("Volume Listener: " + str(result))
        try:
            self._volume = int(result)
        except (ValueError, TypeError):
            pass
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def albumart_listener(self, msg):
        """Listen for the Album Art change"""
        self._album_art = base64.b64decode(msg.payload.replace("\n", ""))
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def state_listener(self, event, updates):
        """Listen for Player State changes (legacy boolean)"""
        result = updates.pop().result
        self._mqtt_player_state = str(result)
        self._state = str(result)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def player_state_listener(self, event, updates):
        """Listen for richer Player State changes (playing/paused/idle/off/buffering)"""
        result = str(updates.pop().result).lower()
        state_map = {
            "playing": STATE_PLAYING,
            "paused": STATE_PAUSED,
            "idle": STATE_IDLE,
            "off": STATE_OFF,
            "buffering": STATE_BUFFERING,
        }
        self._state = state_map.get(result, result)
        self._mqtt_player_state = result
        if result == STATE_PLAYING:
            import datetime
            self._media_position_updated_at = datetime.datetime.now(datetime.timezone.utc)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def shuffle_listener(self, event, updates):
        """Listen for Shuffle state changes"""
        result = str(updates.pop().result).lower()
        self._shuffle = result == "true"
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def repeat_listener(self, event, updates):
        """Listen for Repeat mode changes"""
        result = str(updates.pop().result).lower()
        repeat_map = {
            "all": RepeatMode.ALL,
            "one": RepeatMode.ONE,
            "off": RepeatMode.OFF,
        }
        self._repeat = repeat_map.get(result, RepeatMode.OFF)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def muted_listener(self, event, updates):
        """Listen for Mute state changes"""
        result = str(updates.pop().result).lower()
        self._muted = result == "true"
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def duration_listener(self, event, updates):
        """Listen for media duration changes"""
        result = updates.pop().result
        try:
            self._media_duration = int(result)
        except (ValueError, TypeError):
            pass
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def position_listener(self, event, updates):
        """Listen for media position changes"""
        result = updates.pop().result
        try:
            import datetime
            self._media_position = int(result)
            self._media_position_updated_at = datetime.datetime.now(datetime.timezone.utc)
        except (ValueError, TypeError):
            pass
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def content_type_listener(self, event, updates):
        """Listen for content type changes"""
        result = str(updates.pop().result).lower()
        self._content_type = MediaType.MUSIC if result == "music" else result
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def track_number_listener(self, event, updates):
        """Listen for track number changes"""
        self._track_number = str(updates.pop().result)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def genre_listener(self, event, updates):
        """Listen for genre changes"""
        self._track_genre = str(updates.pop().result)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def album_artist_listener(self, event, updates):
        """Listen for album artist changes"""
        self._track_album_artist = str(updates.pop().result)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    async def year_listener(self, event, updates):
        """Listen for year changes"""
        self._track_year = str(updates.pop().result)
        if MQTTMediaPlayer:
            self.schedule_update_ha_state(True)

    def update(self):
        """ Update the States"""
        if self._player_status_keyword:
            if self._mqtt_player_state == self._player_status_keyword:
                self._state = STATE_PLAYING
            else:
                self._state = STATE_PAUSED

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
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return self._content_type

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
    def media_album_artist(self):
        """Album artist of current playing media."""
        return self._track_album_artist

    @property
    def media_track(self):
        """Track number of current playing media."""
        try:
            return int(self._track_number) if self._track_number else None
        except (ValueError, TypeError):
            return None

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return self._media_duration

    @property
    def media_position(self):
        """Position of current playing media in seconds."""
        return self._media_position

    @property
    def media_position_updated_at(self):
        """When was the position of the current playing media valid."""
        return self._media_position_updated_at

    @property
    def shuffle(self):
        """Boolean if shuffle is enabled."""
        return self._shuffle

    @property
    def repeat(self):
        """Return current repeat mode."""
        return self._repeat

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attrs = {}
        if self._track_genre:
            attrs["genre"] = self._track_genre
        if self._track_year:
            attrs["year"] = self._track_year
        return attrs

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return self._attr_supported_features

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
            self._volume = int(volume * 100)

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

    async def async_media_stop(self):
        """Send media stop command to media player."""
        if(self._stop_script):
            await self._stop_script.async_run(context=self._context)
            self._state = STATE_IDLE

    async def async_media_next_track(self):
        """Send next track command."""
        if(self._next_script):
            await self._next_script.async_run(context=self._context)

    async def async_media_previous_track(self):
        """Send the previous track command."""
        if(self._previous_script):
            await self._previous_script.async_run(context=self._context)

    async def async_set_shuffle(self, shuffle):
        """Enable/disable shuffle mode."""
        if(self._shuffle_set_script):
            await self._shuffle_set_script.async_run({"shuffle": shuffle}, context=self._context)
            self._shuffle = shuffle

    async def async_set_repeat(self, repeat):
        """Set repeat mode."""
        if(self._repeat_set_script):
            repeat_map = {
                RepeatMode.ALL: "all",
                RepeatMode.ONE: "one",
                RepeatMode.OFF: "off",
            }
            mqtt_repeat = repeat_map.get(repeat, "off")
            await self._repeat_set_script.async_run({"repeat": mqtt_repeat}, context=self._context)
            self._repeat = repeat

    async def async_media_seek(self, position):
        """Send seek command."""
        if(self._seek_script):
            await self._seek_script.async_run({"position": int(position)}, context=self._context)
            import datetime
            self._media_position = int(position)
            self._media_position_updated_at = datetime.datetime.now(datetime.timezone.utc)

    async def async_mute_volume(self, mute):
        """Mute the volume."""
        if(self._mute_script):
            await self._mute_script.async_run({"mute": mute}, context=self._context)
            self._muted = mute

    async def async_select_source(self, source):
        """Send source select command."""
        if(self._select_source_script):
            if self._source_list:
                # Static list: look up ID by name
                id_ = None
                for entry in self._source_list:
                    if entry['name'] == source:
                        id_ = entry['id']
                await self._select_source_script.async_run({"source": id_}, context=self._context)
            else:
                # Dynamic: pass source name directly
                await self._select_source_script.async_run({"source": source}, context=self._context)
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