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
* play_media


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
    play_media:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/play_media"
        payload: "{{media}}"

```

## Options

| Variables      | Type                                                                      | Default  | Description                                                                       | Expected Payload            | Example                                                                 |
|----------------|---------------------------------------------------------------------------|----------|-----------------------------------------------------------------------------------|-----------------------------|-------------------------------------------------------------------------|
| name           | string                                                                    | required | Name for the entity                                                               | string                      | ```"Musicbee"```                                                        |
| song_title     | [template](https://www.home-assistant.io/integrations/template/)                                                                    | optional | Value for the song title                                             | string                      | * see configuration.yaml ex.                                              |
| song_artist    | [template](https://www.home-assistant.io/integrations/template/)                                                                    | optional | Value for the song artist                                            | string                      | * see configuration.yaml ex.                                                 |
| song_album     | [template](https://www.home-assistant.io/integrations/template/)                                                                    | optional | Value for the song album                                        | string                      | * see configuration.yaml ex.                                                  |
| song_volume    | [template](https://www.home-assistant.io/integrations/template/)                                                                    | optional | Value for the player volume                                          | int (0 to 100)       | * see configuration.yaml ex.                                                 |
| album_art      | string                                                                    | optional | Topic to listen to for the song album art (Must be a base64 encoded string)       | string (base64 encoded url) | ```"musicbee/albumart"```                                               |
| player_status  | [template](https://www.home-assistant.io/integrations/template/)                                                                    | optional | Value for the player status                         | string                      | * see configuration.yaml ex.                                          |
| vol_down*          | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.volume_down command                           | N/A                         | * see configuration.yaml ex.                                                |
| vol_up*          | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.volume_up command                           | N/A                         | * see configuration.yaml ex.                                                |
| volume      | [service call](https://www.home-assistant.io/docs/scripts/service-calls/)                                                                    | optional | MQTT service to call for the media_player.volume_set command                                    | string                      | * see configuration.yaml                                                |
| play_media  | [service call](https://www.home-assistant.io/docs/scripts/service-calls/)                                                                    | optional | MQTT service to call for the media_player.play_media command                                    | string                      | * see configuration.yaml                                                |
| status_keyword* | string                                                                    | optional | Keyword used to indicate your MQTT enabled player is currently playing a song     | string                      | ```"true"```                                                            |
| next           | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "next" button is pressed                            | N/A                         | * see configuration.yaml ex.                                                |
| previous       | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "previous" button is pressed                        | N/A                         | * see configuration.yaml ex.                                                |
| play           | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "play" button is pressed                            | N/A                         | * see configuration.yaml ex.                                                |
| pause          | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "pause" button is pressed                           | N/A                         | * see configuration.yaml ex.                                                |

*NOTES:

 * volume: put your custom payload here and replace where your value would be with ``"{{volume}}"`` (see config ex.)
 * play_media: put your custom payload here and replace where your value would be with ``"{{media}}"`` (see config ex.)
 * status_keyword: This is the keyword your player publishes when it is PLAYING. You only need to mention the keyword for playing. For example, my player indicates it is playing by publishing ```playing = true``` to my broker. Therefore I enter ```"true"``` in my configuration.yaml
 * vol_up/vol_down: Setting this disables the volume_set service. Use vol_up/vol_down if your media player doesn't publish a volume level (i.e if your media player only responds to simple "volumeup"/"volumedown" commands. **If you use the "volume" topic you DONT need to use vol_up/vol_down. Same for the reverse**
 
 

## Example MQTT Broker
A sensor `sensor.media_info` must be created from the topic `lnxlink/desktop-linux/monitor/stats/media/info` with the following attributes:
```
{
	"title": "Kickapoo",
	"artist": "Tenacious D",
	"album": "",
	"status": "playing",
	"volume": 80,
	"playing": true
}
```
