Computer-vision friendly annotation schema

# Equipment

Nature:
- military
- civilian

Domain:
- land
- sea
- sub-surface
- air
- space


Mobility
- mobile
- semi-mobile
- fixed

## Military vehicle

Function:
- fighting
- artillery
- engineering
- command/communications
- electronic warfare
- logistical
- missile launcher
- CBRN
- radar

Chassis
- wheeled|tracked|half-tracked
- armored|unarmored
- manned|unmanned
- amphibious?
- articulated?
- truck?

Wheeled parameters
- number of axles

Tracked parameters
- number of road wheels

Truck parameters
- Cabin: behind-engine/long-nosed|forward control, flat-face|forward-control, split cab|forward control, left-offset cab|forward control, right-offset cab
- Box body?: chamfered|arched|loaf|flat roof

### Examples

{
  "variant": "obr. 2022",
  "model": "T-72B3",
  "series": "T-72",
  "role": "main_battle_tank",
  "function": "fighting_vehicle",
  "chassis": {
    "mobility": "self-propelled",
    "road_wheels": 6,
    "propulsion": "tracked",
    "modifiers": "armored",
  }
}

{
  "model": "9P78-1",
  "system": "9K270 Iskander-M",
  "role": "transporter-erector-launcher",
  "function": "surface-to-surface_missile_launcher_vehicle", 
  "chassis": {
    "mobility": "self-propelled",
    "propulsion": "wheeled",
    "axles": 4,
    "cab": ["vertical", "flat", "ahead_of_front_axle"],
    "engine_position": "mid"
  }
}

## Civilian vehicle

Function
- passenger car

Passenger car body styles
- buggy
- convertible
- coupé
- fastback
- hatchback
- microvan
- minivan
- panel van
- panel truck
- pickup truck
- sedan
- shooting-brake
- station wagon
- targa top
- ute/coupe utility
