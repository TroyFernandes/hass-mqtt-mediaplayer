# hass-mqtt-mediaplayer

Allows you to use MQTT topics to fill out the information needed for the Home Assistant Media Player Entity

## Supported Services

[Media Player Entity](https://www.home-assistant.io/integrations/media_player/)

* volume_up
* volume_down
* volume_set
* media_play_pause
* media_play
* media_pause
* media_next_track
* media_previous_track


## Installation
Easiest install is via [HACS](https://hacs.xyz/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bkbilly&repository=hass-mqtt-mediaplayer&category=integration)


## Example configuration.yaml

```yaml
media_player:  
  - platform: mqtt-mediaplayer
    name: "Musicbee"
    topic:
      song_title: "{{ states('sensor.musicbee_nowplaying_songtitle') }}"
      song_artist: "{{ states('sensor.musicbee_nowplaying_artist') }}"
      song_album: "{{ states('sensor.musicbee_nowplaying_album') }}"
      song_volume: "{{ states('sensor.musicbee_nowplaying_playervolume') }}"
      player_status: "{{ states('sensor.musicbee_playingstatus') }}"
      album_art: "musicbee/albumart"
      volume:
        service: mqtt.publish
        data:
          topic: "musicbee/command"
          payload: "{\"command\":\"volume_set\", \"args\":{\"volume\":\"{{volume}}\"}}"
    status_keyword: "true"
    next:
      service: mqtt.publish
      data:
        topic: "musicbee/command"
        payload: "{\"command\": \"next\"}"
    previous:
      service: mqtt.publish
      data:
        topic: "musicbee/command"
        payload: "{\"command\": \"previous\"}"
    play:
      service: mqtt.publish
      data:
        topic: "musicbee/command"
        payload: "{\"command\": \"play\"}"
    pause:
      service: mqtt.publish
      data:
        topic: "musicbee/command"
        payload: "{\"command\": \"pause\"}"

```
