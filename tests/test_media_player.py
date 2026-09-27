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


async def setup_player(hass, mqtt_mock):
    """Set up the platform and return the created entity state."""
    assert await async_setup_component(hass, DOMAIN, BASE_CONFIG)
    await hass.async_block_till_done()
    state = hass.states.get(PLAYER)
    assert state is not None, "media player entity was not created"
    return state


async def test_setup(hass, mqtt_mock):
    """Platform sets up and registers the entity with expected features."""
    state = await setup_player(hass, mqtt_mock)
    assert state.name == "Test Player"

    feats = state.attributes["supported_features"]
    assert MediaPlayerEntityFeature.PLAY in feats
    assert MediaPlayerEntityFeature.PAUSE in feats


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
