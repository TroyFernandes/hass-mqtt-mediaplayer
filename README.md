# hass-mqtt-mediaplayer

Allows you to use MQTT topics to fill out the information needed for the Home Assistant Media Player Entity

## Supported Services

[Media Player Entity](https://www.home-assistant.io/integrations/media_player/)

* volume_up
* volume_down
* volume_set
* volume_mute
* media_play_pause
* media_stop
* media_play
* media_pause
* media_next_track
* media_previous_track
* shuffle_set
* repeat_set
* select_source

## Options

| Variables | Type | Default | Description | Expected Payload | Example |
|---|---|---|---|---|---|
| name | string | required | Name for the entity | string | ```"Musicbee"``` |
| **Player State** |
| player_state | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the player state (playing/paused/idle/off/buffering) | string | * see configuration.yaml ex. |
| player_status | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the player status (legacy) | string | * see configuration.yaml ex. |
| status_keyword* | string | optional | Keyword used to indicate your MQTT enabled player is currently playing a song | string | ```"true"``` |
| shuffle_mode | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the shuffle state | bool (true/false) | * see configuration.yaml ex. |
| repeat_mode | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the repeat mode | string (off/one/all) | * see configuration.yaml ex. |
| muted | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the mute state | bool (true/false) | * see configuration.yaml ex. |
| song_volume | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the player volume | int (0 to 100) | * see configuration.yaml ex. |
| media_duration | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the song duration in seconds | int | * see configuration.yaml ex. |
| media_position | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the current playback position in seconds | int | * see configuration.yaml ex. |
| **Song Info** |
| song_title | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the song title | string | * see configuration.yaml ex. |
| song_artist | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the song artist | string | * see configuration.yaml ex. |
| song_album | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the song album | string | * see configuration.yaml ex. |
| album_artist | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the album artist | string | * see configuration.yaml ex. |
| album_art | string | optional | Topic to listen to for the song album art (Must be a base64 encoded string) | string (base64 encoded) | ```"musicbee/albumart"``` |
| genre | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the song genre | string | * see configuration.yaml ex. |
| year | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the release year | string | * see configuration.yaml ex. |
| track_number | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the track number | int | * see configuration.yaml ex. |
| content_type | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the media content type | string | * see configuration.yaml ex. |
| **Source** |
| source | [template](https://www.home-assistant.io/integrations/template/) | optional | Value for the currently active source | string | * see configuration.yaml ex. |
| source_list | string or list | optional | MQTT topic publishing a JSON array of source names, or a static list of id/name objects | JSON array or list | ```"musicbee/player/output_devices"``` |
| **Playback Controls** |
| play | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "play" button is pressed | N/A | * see configuration.yaml ex. |
| pause | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "pause" button is pressed | N/A | * see configuration.yaml ex. |
| stop | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "stop" button is pressed | N/A | * see configuration.yaml ex. |
| next | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "next" button is pressed | N/A | * see configuration.yaml ex. |
| previous | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call when the "previous" button is pressed | N/A | * see configuration.yaml ex. |
| seek | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.media_seek command | N/A | * see configuration.yaml ex. |
| shuffle_set | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.shuffle_set command | N/A | * see configuration.yaml ex. |
| repeat_set | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.repeat_set command | N/A | * see configuration.yaml ex. |
| **Volume Controls** |
| volume | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.volume_set command | string | * see configuration.yaml |
| vol_up* | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.volume_up command | N/A | * see configuration.yaml ex. |
| vol_down* | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.volume_down command | N/A | * see configuration.yaml ex. |
| mute | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.volume_mute command | N/A | * see configuration.yaml ex. |
| **Source Control** |
| select_source | [service call](https://www.home-assistant.io/docs/scripts/service-calls/) | optional | MQTT service to call for the media_player.select_source command | N/A | * see configuration.yaml ex. |

*NOTES:

 * volume: put your custom payload here and replace where your value would be with ``"{{volume}}"`` (see config ex.)
 * status_keyword: This is the keyword your player publishes when it is PLAYING. You only need to mention the keyword for playing. For example, my player indicates it is playing by publishing ```playing = true``` to my broker. Therefore I enter ```"true"``` in my configuration.yaml
 * vol_up/vol_down: Setting this disables the volume_set service. Use vol_up/vol_down if your media player doesn't publish a volume level (i.e if your media player only responds to simple "volumeup"/"volumedown" commands. **If you use the "volume" topic you DONT need to use vol_up/vol_down. Same for the reverse**
 
 
 
## Example configuration.yaml

```yaml
media_player:  
- platform: mqtt-mediaplayer
  name: "Musicbee"
  topic:
    song_title: "{{ states('sensor.musicbee_song_title') }}"
    song_artist: "{{ states('sensor.musicbee_song_artist') }}"
    song_album: "{{ states('sensor.musicbee_song_album') }}"
    song_volume: "{{ states('sensor.musicbee_player_volume') }}"
    player_state: "{{ states('sensor.musicbee_player_state') }}"
    shuffle_mode: "{{ states('sensor.musicbee_shuffle_mode') }}"
    repeat_mode: "{{ states('sensor.musicbee_repeat_mode') }}"
    muted: "{{ states('sensor.musicbee_muted') }}"
    media_duration: "{{ states('sensor.musicbee_song_duration') }}"
    media_position: "{{ states('sensor.musicbee_player_progress') }}"
    content_type: "{{ states('sensor.musicbee_content_type') }}"
    track_number: "{{ states('sensor.musicbee_song_track') }}"
    genre: "{{ states('sensor.musicbee_song_genre') }}"
    album_artist: "{{ states('sensor.musicbee_song_album_artist') }}"
    year: "{{ states('sensor.musicbee_song_year') }}"
    album_art: "musicbee/song/albumart"
    source: "{{ states('sensor.musicbee_output_device') }}"
    source_list: "musicbee/player/output_devices"

    volume:
      service: mqtt.publish
      data:
        topic: "musicbee/command"
        payload: "{\"command\":\"volume_set\", \"args\":{\"volume\":\"{{volume}}\"}}"
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
  stop:
    service: mqtt.publish
    data:
      topic: "musicbee/command"
      payload: "{\"command\": \"stop\"}"
  shuffle_set:
    service: mqtt.publish
    data:
      topic: "musicbee/command"
      payload: "{\"command\":\"shuffle_set\", \"args\":{\"shuffle\":{{shuffle|tojson}}}}"
  repeat_set:
    service: mqtt.publish
    data:
      topic: "musicbee/command"
      payload: "{\"command\":\"repeat_set\", \"args\":{\"repeat\":\"{{repeat}}\"}}"
  seek:
    service: mqtt.publish
    data:
      topic: "musicbee/command"
      payload: "{\"command\":\"seek\", \"args\":{\"position\":{{position}}}}"
  mute:
    service: mqtt.publish
    data:
      topic: "musicbee/command"
      payload: "{\"command\":\"mute_set\", \"args\":{\"mute\":{{mute|tojson}}}}"
  select_source:
    service: mqtt.publish
    data:
      topic: "musicbee/command"
      payload: "{\"command\":\"select_source\", \"args\":{\"source\":\"{{source}}\"}}"

```

## Example MQTT Broker

This is what my player outputs and what I see when I use MQTT Explorer

```
musicbee
    ➤ player
        status = online
        state = playing
        output_devices = ["Primary Sound Driver", "Speakers"]
        output_device = Primary Sound Driver
        progress = 99
        volume = 73
        file = C:\Users\Troy\Music\Main\SZA\SOS\Far.flac
        position = 232
        shuffle = true
        repeat = off
        muted = false
    ➤ song
        album = SOS
        albumart = /9j/4AAQSkZJRgABAQEBLAEsAAD/2wBDAAgGBgcGBQg ...
        title = Far
        artist = SZA
        info = FLAC 44.1 kHz, 1502k
        duration = 264
        track = 22
        albumartist = SZA
        year = February 6, 2026
        content_type = music
        genre = Hip Hop
    command = {"command": "pause"}
```
