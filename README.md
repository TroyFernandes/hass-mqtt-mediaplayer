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

## Example customize.yaml
```yaml
media_player:  
  - platform: mqtt-mediaplayer
    name: "Musicbee"
    topic:
      song_title: "musicbee/songtitle"
      song_artist: "musicbee/artist"
      song_album: "musicbee/album"
      song_volume: "musicbee/volume"
      album_art: "musicbee/albumart"
      player_status: "musicbee/playing"
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
