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
    name: "Desktop Linux"
    status_keyword: "true"
    topic:
      song_title: "{{ state_attr('sensor.media_info', 'title') }}"
      song_artist: "{{ state_attr('sensor.media_info', 'artist') }}"
      song_album: "{{ state_attr('sensor.media_info', 'album') }}"
      song_volume: "{{ state_attr('sensor.media_info', 'volume') }}"
      player_status: "{{ state_attr('sensor.media_info', 'status') }}"
      volume:
        service: mqtt.publish
        data:
          topic: "lnxlink/desktop-linux/commands/media/volume_set"
          payload: "{{volume}}"
    next:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/next"
        payload: "ON"
    previous:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/previous"
        payload: "ON"
    play:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/playpause"
        payload: "ON"
    pause:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/playpause"
        payload: "ON"

```
