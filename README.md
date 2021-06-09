# VacuumZones

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

[Home Assistant](https://www.home-assistant.io/) custom component that helps control zone cleaning for [Xiaomi Vacuum](https://www.home-assistant.io/integrations/xiaomi_miio/#xiaomi-mi-robot-vacuum) cleaners with the help of voice assistants - Apple Siri, Google Assistant, Yandex Alice.

This component creates a virtual vacuum cleaner for each of your zone or room.

By adding these vacuums to your voice assistant, you can give voice commands, like "clean bedroom". If your voice assistant supports multiple device commands - you can say "clean up the hall and under the table".

All cleaning commands are **added to the queue**. The vacuum cleaner will start a new room only after it has finished the previous. Cleaning the next room starts when the vacuum goes into `returning` or `docked` state.

Current zone will be in `cleaning` state, next zones will be in `paused` state, other zones will be in `idle` state.

You can pause main vacuum entity, it won't reset the queue. You can stop any of the virtual vacuum cleaners - this will reset the queue, but will not stop cleaning in the current room. You can skip the current room by sending the main vacuum cleaner to the dock, the integration will automatically start the next element of the queue.

## Installation

**Method 1.** [HACS](https://hacs.xyz/) custom repo:

> HACS > Integrations > 3 dots (upper top corner) > Custom repositories > URL: `AlexxIT/VacuumZones`, Category: Integration > Add > wait > VacuumZones > Install

**Method 2.** Manually copy `vacuum_zones` folder from [latest release](https://github.com/AlexxIT/VacuumZones/releases/latest) to `/config/custom_components` folder.

## Configuration

You can config each room/zone with a [room number](https://www.home-assistant.io/integrations/xiaomi_miio/#service-xiaomi_miiovacuum_clean_segment) or with a [zone coordinates](https://www.home-assistant.io/integrations/xiaomi_miio/#service-xiaomi_miiovacuum_clean_zone).

Check [this integration](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Xiaomi-Cloud-Map-Extractor) and [this app](https://xiaomi.flole.de/) for coordinates extraction.

You can use [this integration](https://github.com/AlexxIT/XiaomiGateway3#obtain-mi-home-device-token) for extract rooms with names if your vacuum support it. **S5 Max** - support rooms with names, **S5** - don't support names for rooms.

You can use multiple rooms/zones in one zone item.

`configuration.yaml` example:

```yaml
vacuum_zones:
  entity_id: vacuum.roborock_vacuum_s5e  # change to your vacuum
  zones:
    Hall:  # room name on your language
      room: 20  # one or more rooms

    Under the table:  # zone name on your language
      zone: [[23510,25311,25110,26361]]  # one or more zones
      repeats: 2  # optional, default 1

    Home:  # zone name on your language
      sequence:  # optional script sequence (run before command to vacuum)
      - service: persistent_notification.create
        data:
          message: Starting a complete house cleaning
      room: [15,16,17]

    Trash:  # point name on your language
      goto: [25500, 25500]  # move to point
```

## Useful links

- [Xiaomi Gateway 3](https://github.com/AlexxIT/XiaomiGateway3#obtain-mi-home-device-token) - extract Mi Home tokens from Home Assistant GUI 
- [Xiaomi Cloud Map Extractor](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Xiaomi-Cloud-Map-Extractor) - life map for your vacuum
- [Xiaomi Vacuum Map Card](https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card) - lovelace map card
- [Vacuum Card](https://github.com/denysdovhan/vacuum-card) - lovelace vacuum card
