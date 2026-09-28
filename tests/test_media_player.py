"""Tests for the mqtt-mediaplayer media_player platform."""
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.components.mqtt import async_subscribe
from homeassistant.const import STATE_IDLE, STATE_OFF, STATE_PAUSED, STATE_PLAYING
from pytest_homeassistant_custom_component.common import async_setup_component

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
