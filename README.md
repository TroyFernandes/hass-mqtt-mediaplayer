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

## Options

| Variables       | Type                                                                          | Default  | Description                                                                       | Expected Payload            | Example                                                                 |
|-----------------|-------------------------------------------------------------------------------|----------|-----------------------------------------------------------------------------------|-----------------------------|-------------------------------------------------------------------------|
| name            | string                                                                        | required | Name for the entity                                                               | string                      | ```"Musicbee"```                                                        |
| song_title      | [template](https://www.home-assistant.io/integrations/template/)              | optional | Value for the song title                                                          | string                      | * see configuration.yaml ex.                                            |
| song_artist     | [template](https://www.home-assistant.io/integrations/template/)              | optional | Value for the song artist                                                         | string                      | * see configuration.yaml ex.                                            |
| song_album      | [template](https://www.home-assistant.io/integrations/template/)              | optional | Value for the song album                                                          | string                      | * see configuration.yaml ex.                                            |
| song_volume     | [template](https://www.home-assistant.io/integrations/template/)              | optional | Value for the player volume                                                       | int (0 to 100)              | * see configuration.yaml ex.                                            |
| player_status   | [template](https://www.home-assistant.io/integrations/template/)              | optional | Value for the player status. Supports "idle", "playing", "idle", "off"            | string                      | * see configuration.yaml ex.                                            |
| volume          | [service call](https://www.home-assistant.io/docs/scripts/service-calls/)     | optional | MQTT service to call for the media_player.volume_set command                      | string                      | * see configuration.yaml                                                |
| status_keyword* | string                                                                        | optional | Keyword used to indicate your MQTT enabled player is currently playing a song     | string                      | ```"true"```                                                            |
| next            | [service call](https://www.home-assistant.io/docs/scripts/service-calls/)     | optional | MQTT service to call when the "next" button is pressed                            | N/A                         | * see configuration.yaml ex.                                            |
| previous        | [service call](https://www.home-assistant.io/docs/scripts/service-calls/)     | optional | MQTT service to call when the "previous" button is pressed                        | N/A                         | * see configuration.yaml ex.                                            |
| play            | [service call](https://www.home-assistant.io/docs/scripts/service-calls/)     | optional | MQTT service to call when the "play" button is pressed                            | N/A                         | * see configuration.yaml ex.                                            |
| pause           | [service call](https://www.home-assistant.io/docs/scripts/service-calls/)     | optional | MQTT service to call when the "pause" button is pressed                           | N/A                         | * see configuration.yaml ex.                                            |

*NOTES:

 * volume: put your custom payload here and replace where your value would be with ``"{{volume}}"`` (see config ex.)
 * status_keyword: This is the keyword your player publishes when it is PLAYING. You only need to mention the keyword for playing. For example, my player indicates it is playing by publishing ```playing = true``` to my broker. Therefore I enter ```"true"``` in my configuration.yaml
 * vol_up/vol_down: Setting this disables the volume_set service. Use vol_up/vol_down if your media player doesn't publish a volume level (i.e if your media player only responds to simple "volumeup"/"volumedown" commands. **If you use the "volume" topic you DONT need to use vol_up/vol_down. Same for the reverse**
 
 
 
## Example configuration.yaml

```yaml
  - platform: mqtt-mediaplayer
    name: "Desktop"
    status_keyword: "true"
    topic:
      song_title: "{{ state_attr('sensor.desktop_media_player', 'title') }}"
      song_artist: "{{ state_attr('sensor.desktop_media_player', 'artist') }}"
      song_album: "{{ state_attr('sensor.desktop_media_player', 'album') }}"
      song_volume: "{{ state_attr('sensor.desktop_media_player', 'volume') }}"
      player_status: "{{ state_attr('sensor.desktop_media_player', 'status') }}"
      # player_status: "{{ states('sensor.desktop_media_player') }}"
      volume:
        service: mqtt.publish
        data:
          topic: "iotlink/workgroup/desktop/commands/media/volume_set"
          payload: "{{volume}}"
    next:
      service: mqtt.publish
      data:
        topic: "iotlink/workgroup/desktop/commands/media/next"
        payload: "ON"
    previous:
      service: mqtt.publish
      data:
        topic: "iotlink/workgroup/desktop/commands/media/previous"
        payload: "ON"
    play:
      service: mqtt.publish
      data:
        topic: "iotlink/workgroup/desktop/commands/media/playpause"
        payload: "ON"
    pause:
      service: mqtt.publish
      data:
        topic: "iotlink/workgroup/desktop/commands/media/playpause"
        payload: "ON"
```

## Example MQTT Broker

This is what my player outputs and what I see when I use MQTT Explorer

```json
{
  "title": "Amy Pond: Best Moments (Part One) | Doctor Who",
  "artist": "Doctor Who",
  "album": "",
  "status": "playing",
  "volume": 58,
  "playing": true
}
```
