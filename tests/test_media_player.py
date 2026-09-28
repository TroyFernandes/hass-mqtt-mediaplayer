"""Tests for the mqtt-mediaplayer media_player platform."""
import json

from homeassistant.components.media_player import MediaPlayerEntityFeature, RepeatMode
from homeassistant.components.mqtt import async_subscribe
from homeassistant.const import STATE_IDLE, STATE_OFF, STATE_PAUSED, STATE_PLAYING
from pytest_homeassistant_custom_component.common import async_fire_mqtt_message, async_setup_component

DOMAIN = "media_player"
PLAYER = "media_player.test_player"

BASE_CONFIG = {
    DOMAIN: {
        "platform": "mqtt-mediaplayer",
        "name": "Test Player",
        "topic": {
            "song_title": "{{ states('input_text.title') }}",
            "song_artist": "{{ states('input_text.artist') }}",
            "player_state": "{{ states('input_select.state') }}",
        },
        "play": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/play", "payload": "play"},
        },
        "pause": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/pause", "payload": "pause"},
        },
    }
}


def _text(payload):
    return payload.decode() if isinstance(payload, bytes) else payload


async def setup_player(hass, mqtt_mock, config=BASE_CONFIG):
    """Set up the platform and return the created entity state."""
    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    state = hass.states.get(PLAYER)
    assert state is not None, "media player entity was not created"
    return state


async def test_setup(hass, mqtt_mock):
    """Platform sets up and registers the entity with expected features."""
    state = await setup_player(hass, mqtt_mock)
    assert state.name == "Test Player"

    feats = state.attributes["supported_features"]
    assert feats & MediaPlayerEntityFeature.PLAY
    assert feats & MediaPlayerEntityFeature.PAUSE


async def test_media_title_updates(hass, mqtt_mock):
    """song_title template drives the media_title attribute."""
    await setup_player(hass, mqtt_mock)

    hass.states.async_set("input_text.title", "Song One")
    await hass.async_block_till_done()
    assert hass.states.get(PLAYER).attributes["media_title"] == "Song One"

    hass.states.async_set("input_text.title", "Song Two")
    await hass.async_block_till_done()
    assert hass.states.get(PLAYER).attributes["media_title"] == "Song Two"


async def test_media_artist_updates(hass, mqtt_mock):
    """song_artist template drives the media_artist attribute."""
    await setup_player(hass, mqtt_mock)

    hass.states.async_set("input_text.artist", "The Band")
    await hass.async_block_till_done()
    assert hass.states.get(PLAYER).attributes["media_artist"] == "The Band"


async def test_player_state_maps(hass, mqtt_mock):
    """player_state template maps to the HA player state."""
    await setup_player(hass, mqtt_mock)

    for raw, expected in [
        ("playing", STATE_PLAYING),
        ("paused", STATE_PAUSED),
        ("idle", STATE_IDLE),
        ("off", STATE_OFF),
    ]:
        hass.states.async_set("input_select.state", raw)
        await hass.async_block_till_done()
        assert hass.states.get(PLAYER).state == expected


async def test_media_play_publishes(hass, mqtt_mock):
    """media_play service runs the play script which publishes to MQTT."""
    await setup_player(hass, mqtt_mock)

    received = []
    await async_subscribe(hass, "cmd/play", lambda msg: received.append(_text(msg.payload)))
    await hass.services.async_call("media_player", "media_play", {"entity_id": PLAYER}, blocking=True)
    await hass.async_block_till_done()
    assert received == ["play"]


async def test_media_pause_publishes(hass, mqtt_mock):
    """media_pause service runs the pause script which publishes to MQTT."""
    await setup_player(hass, mqtt_mock)

    received = []
    await async_subscribe(hass, "cmd/pause", lambda msg: received.append(_text(msg.payload)))
    await hass.services.async_call("media_player", "media_pause", {"entity_id": PLAYER}, blocking=True)
    await hass.async_block_till_done()
    assert received == ["pause"]


VOLUME_CONFIG = {
    DOMAIN: {
        **BASE_CONFIG[DOMAIN],
        "topic": {
            **BASE_CONFIG[DOMAIN]["topic"],
            "volume": {
                "action": "mqtt.publish",
                "data": {"topic": "cmd/volume", "payload": "{{ volume }}"},
            },
        },
    }
}


SOURCE_CONFIG = {
    DOMAIN: {
        **BASE_CONFIG[DOMAIN],
        "topic": {
            **BASE_CONFIG[DOMAIN]["topic"],
            "source": "{{ states('input_text.source_id') }}",
            "source_list": [
                {"id": "spotify", "name": "Spotify"},
                {"id": "aux1", "name": "Aux 1"},
            ],
        },
        "select_source": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/source", "payload": "{{ source }}"},
        },
    }
}


async def test_volume_up_stays_in_range(hass, mqtt_mock):
    """media_volume_up keeps volume_level within 0..1 after repeated calls."""
    assert await async_setup_component(hass, DOMAIN, VOLUME_CONFIG)
    await hass.async_block_till_done()
    entity = next(iter(hass.data[DOMAIN]._entities.values()))

    for _ in range(5):
        await hass.services.async_call(
            "media_player", "volume_up", {"entity_id": PLAYER}, blocking=True
        )
        await hass.async_block_till_done()
        assert 0.0 <= entity.volume_level <= 1.0


async def test_volume_down_stays_in_range(hass, mqtt_mock):
    """media_volume_down keeps volume_level within 0..1 after repeated calls."""
    assert await async_setup_component(hass, DOMAIN, VOLUME_CONFIG)
    await hass.async_block_till_done()
    entity = next(iter(hass.data[DOMAIN]._entities.values()))

    for _ in range(5):
        await hass.services.async_call(
            "media_player", "volume_down", {"entity_id": PLAYER}, blocking=True
        )
        await hass.async_block_till_done()
        assert 0.0 <= entity.volume_level <= 1.0

async def test_select_source_with_string_id(hass, mqtt_mock):
    """Selecting a source with a non-numeric id publishes the id and updates state."""
    assert await async_setup_component(hass, DOMAIN, SOURCE_CONFIG)
    await hass.async_block_till_done()

    received = []
    await async_subscribe(hass, "cmd/source", lambda msg: received.append(_text(msg.payload)))
    await hass.services.async_call(
        "media_player", "select_source", {"entity_id": PLAYER, "source": "Spotify"}, blocking=True
    )
    await hass.async_block_till_done()
    entity = next(iter(hass.data[DOMAIN]._entities.values()))
    assert received == ["spotify"]
    assert entity.source == "Spotify"


async def test_source_listener_resolves_string_id(hass, mqtt_mock):
    """source_listener maps a non-numeric incoming id to its name without raising."""
    assert await async_setup_component(hass, DOMAIN, SOURCE_CONFIG)
    await hass.async_block_till_done()

    hass.states.async_set("input_text.source_id", "spotify")
    await hass.async_block_till_done()
    assert hass.states.get(PLAYER).attributes["source"] == "Spotify"

LEAK_CONFIG = {
    DOMAIN: {
        **BASE_CONFIG[DOMAIN],
        "topic": {
            **BASE_CONFIG[DOMAIN]["topic"],
            "album_art": "cmd/album_art",
            "source_list": "cmd/source_list",
        },
    }
}


async def test_subscriptions_cleaned_up_on_unload(hass, mqtt_mock):
    """album_art and source_list MQTT subscriptions are removed when the entity unloads."""
    assert await async_setup_component(hass, DOMAIN, LEAK_CONFIG)
    await hass.async_block_till_done()
    assert mqtt_mock._simple_subscriptions.get("cmd/album_art")
    assert mqtt_mock._simple_subscriptions.get("cmd/source_list")
    platform = next(
        p for p in hass.data[DOMAIN]._platforms.values()
        if PLAYER in p.entities
    )
    await platform.async_remove_entity(PLAYER)
    await hass.async_block_till_done()
    assert not mqtt_mock._simple_subscriptions.get("cmd/album_art")
    assert not mqtt_mock._simple_subscriptions.get("cmd/source_list")
    assert hass.states.get(PLAYER) is None


FEATURE_CONFIG = {
    DOMAIN: {
        **BASE_CONFIG[DOMAIN],
        "stop": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/stop", "payload": "1"},
        },
        "turn_on": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/turn_on", "payload": "1"},
        },
        "turn_off": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/turn_off", "payload": "1"},
        },
        "shuffle_set": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/shuffle", "payload": "{{ shuffle }}"},
        },
        "repeat_set": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/repeat", "payload": "{{ repeat }}"},
        },
        "seek": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/seek", "payload": "{{ position }}"},
        },
        "mute": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/mute", "payload": "{{ mute }}"},
        },
    }
}


async def test_action_config_sets_feature_flags(hass, mqtt_mock):
    """Each configured action adds its MediaPlayerEntityFeature flag."""
    state = await setup_player(hass, mqtt_mock, config=FEATURE_CONFIG)
    feats = state.attributes["supported_features"]
    for flag in (
        MediaPlayerEntityFeature.STOP,
        MediaPlayerEntityFeature.TURN_ON,
        MediaPlayerEntityFeature.TURN_OFF,
        MediaPlayerEntityFeature.SHUFFLE_SET,
        MediaPlayerEntityFeature.REPEAT_SET,
        MediaPlayerEntityFeature.SEEK,
        MediaPlayerEntityFeature.VOLUME_MUTE,
    ):
        assert feats & flag, f"missing {flag.name}"


async def test_media_seek_round_trip(hass, mqtt_mock):
    """media_seek publishes the position and updates media_position."""
    await setup_player(hass, mqtt_mock, config=FEATURE_CONFIG)
    entity = next(iter(hass.data[DOMAIN]._entities.values()))

    received = []
    await async_subscribe(hass, "cmd/seek", lambda msg: received.append(_text(msg.payload)))
    await hass.services.async_call(
        "media_player", "media_seek", {"entity_id": PLAYER, "seek_position": 90}, blocking=True
    )
    await hass.async_block_till_done()

    assert received == ["90"]
    assert entity.media_position == 90
    assert entity.media_position_updated_at is not None


async def test_repeat_shuffle_mute_round_trip(hass, mqtt_mock):
    """repeat/shuffle/mute handlers publish expected payloads and update state."""
    await setup_player(hass, mqtt_mock, config=FEATURE_CONFIG)
    entity = next(iter(hass.data[DOMAIN]._entities.values()))

    received = {"cmd/repeat": [], "cmd/shuffle": [], "cmd/mute": []}
    for topic, bucket in received.items():
        await async_subscribe(
            hass, topic, lambda msg, b=bucket: b.append(_text(msg.payload))
        )

    await entity.async_set_repeat(RepeatMode.ONE)
    await entity.async_set_shuffle(True)
    await entity.async_mute_volume(True)
    await hass.async_block_till_done()

    assert received["cmd/repeat"] == ["one"]
    assert received["cmd/shuffle"] == ["True"]
    assert received["cmd/mute"] == ["True"]
    assert entity.repeat == RepeatMode.ONE
    assert entity.shuffle is True
    assert entity.is_volume_muted is True


DYN_SOURCE_CONFIG = {
    DOMAIN: {
        **BASE_CONFIG[DOMAIN],
        "topic": {
            **BASE_CONFIG[DOMAIN]["topic"],
            "source": "{{ states('input_text.source_id') }}",
            "source_list": "cmd/source_list",
        },
        "select_source": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/source", "payload": "{{ source }}"},
        },
    }
}


async def test_dynamic_source_list_from_mqtt(hass, mqtt_mock):
    """Publishing a JSON array to the source_list topic updates source_list."""
    await setup_player(hass, mqtt_mock, config=DYN_SOURCE_CONFIG)

    async_fire_mqtt_message(hass, "cmd/source_list", json.dumps(["Spotify", "Aux 1", "TuneIn"]))
    await hass.async_block_till_done()
    assert hass.states.get(PLAYER).attributes["source_list"] == [
        "Spotify",
        "Aux 1",
        "TuneIn",
    ]


ALL_TOPICS_CONFIG = {
    DOMAIN: {
        **BASE_CONFIG[DOMAIN],
        "topic": {
            **BASE_CONFIG[DOMAIN]["topic"],
            "song_album": "{{ states('input_text.album') }}",
            "song_volume": "{{ states('input_text.volume') }}",
            "album_art": "cmd/album_art",
            "source": "{{ states('input_text.source') }}",
            "source_list": "cmd/source_list",
            "shuffle_mode": "{{ states('input_select.shuffle') }}",
            "repeat_mode": "{{ states('input_select.repeat') }}",
            "muted": "{{ states('input_select.muted') }}",
            "media_duration": "{{ states('input_text.duration') }}",
            "media_position": "{{ states('input_text.position') }}",
            "content_type": "{{ states('input_text.content_type') }}",
            "track_number": "{{ states('input_text.track_number') }}",
            "genre": "{{ states('input_text.genre') }}",
            "album_artist": "{{ states('input_text.album_artist') }}",
            "year": "{{ states('input_text.year') }}",
        },
        "select_source": {
            "action": "mqtt.publish",
            "data": {"topic": "cmd/source", "payload": "{{ source }}"},
        },
    }
}


async def test_publish_to_every_topic_updates_state(hass, mqtt_mock):
    """Publishing to every configured topic updates the corresponding attribute."""
    await setup_player(hass, mqtt_mock, config=ALL_TOPICS_CONFIG)

    hass.states.async_set("input_text.title", "Song One")
    hass.states.async_set("input_text.artist", "The Band")
    hass.states.async_set("input_text.album", "Album One")
    hass.states.async_set("input_text.volume", "55")
    hass.states.async_set("input_select.state", "playing")
    hass.states.async_set("input_text.source", "Living Room")
    hass.states.async_set("input_select.shuffle", "true")
    hass.states.async_set("input_select.repeat", "all")
    hass.states.async_set("input_select.muted", "true")
    hass.states.async_set("input_text.duration", "245")
    hass.states.async_set("input_text.position", "87")
    hass.states.async_set("input_text.content_type", "music")
    hass.states.async_set("input_text.track_number", "4")
    hass.states.async_set("input_text.genre", "Rock")
    hass.states.async_set("input_text.album_artist", "Album Artists")
    hass.states.async_set("input_text.year", "1999")
    async_fire_mqtt_message(hass, "cmd/album_art", "AAEC")
    async_fire_mqtt_message(hass, "cmd/source_list", json.dumps(["Spotify", "Aux 1"]))
    await hass.async_block_till_done()

    attrs = hass.states.get(PLAYER).attributes
    assert attrs["media_title"] == "Song One"
    assert attrs["media_artist"] == "The Band"
    assert attrs["media_album_name"] == "Album One"
    assert attrs["volume_level"] == 0.55
    assert hass.states.get(PLAYER).state == STATE_PLAYING
    assert attrs["source"] == "Living Room"
    assert attrs["source_list"] == ["Spotify", "Aux 1"]
    assert attrs["shuffle"] is True
    assert attrs["repeat"] == RepeatMode.ALL
    assert attrs["is_volume_muted"] is True
    assert attrs["media_duration"] == 245
    assert attrs["media_position"] == 87
    assert attrs["media_position_updated_at"] is not None
    assert attrs["media_content_type"] == "music"
    assert attrs["media_track"] == 4
    assert attrs["genre"] == "Rock"
    assert attrs["media_album_artist"] == "Album Artists"
    assert attrs["year"] == "1999"
