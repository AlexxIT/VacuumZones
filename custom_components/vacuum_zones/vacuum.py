from homeassistant.components.vacuum import (
    DOMAIN as VACUUM_DOMAIN,
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_SEQUENCE,
    EVENT_STATE_CHANGED,
)
from homeassistant.core import Context, Event, State
from homeassistant.helpers import entity_registry
from homeassistant.helpers.script import Script


async def async_setup_platform(hass, _, async_add_entities, discovery_info=None):
    entity_id: str = discovery_info["entity_id"]
    queue: list[ZoneVacuum] = []
    entities = [
        ZoneVacuum(name, config, entity_id, queue)
        for name, config in discovery_info["zones"].items()
    ]
    async_add_entities(entities)

    async def state_changed_event_listener(event: Event):
        if entity_id != event.data.get(ATTR_ENTITY_ID) or not queue:
            return

        new_state: State = event.data.get("new_state")
        if new_state.state not in (VacuumActivity.RETURNING, VacuumActivity.DOCKED):
            return

        prev: ZoneVacuum = queue.pop(0)
        await prev.internal_stop()

        if not queue:
            return

        next_: ZoneVacuum = queue[0]
        await next_.internal_start(event.context)

    hass.bus.async_listen(EVENT_STATE_CHANGED, state_changed_event_listener)


class ZoneVacuum(StateVacuumEntity):
    _attr_activity = VacuumActivity.IDLE
    _attr_supported_features = VacuumEntityFeature.START | VacuumEntityFeature.STOP

    domain: str = None
    service: str = None
    script: Script = None

    def __init__(self, name: str, config: dict, entity_id: str, queue: list):
        self._attr_name = config.pop("name", name)
        self.service_data: dict = config | {ATTR_ENTITY_ID: entity_id}
        self.queue = queue

    @property
    def vacuum_entity_id(self) -> str:
        return self.service_data[ATTR_ENTITY_ID]

    async def async_added_to_hass(self):
        # init start script
        if sequence := self.service_data.pop(CONF_SEQUENCE, None):
            self.script = Script(self.hass, sequence, self.name, VACUUM_DOMAIN)

        # get entity domain
        # https://github.com/home-assistant/core/blob/dev/homeassistant/components/xiaomi_miio/services.yaml
        # https://github.com/Tasshack/dreame-vacuum/blob/master/custom_components/dreame_vacuum/services.yaml
        # https://github.com/humbertogontijo/homeassistant-roborock/blob/main/custom_components/roborock/services.yaml
        entry = entity_registry.async_get(self.hass).async_get(self.vacuum_entity_id)
        self.domain = entry.platform

        # migrate service field names
        if room := self.service_data.pop("room", None):
            self.service_data["segments"] = room
        if goto := self.service_data.pop("goto", None):
            self.service_data["x_coord"] = goto[0]
            self.service_data["y_coord"] = goto[1]

        if "segments" in self.service_data:
            # "xiaomi_miio", "dreame_vacuum", "roborock"
            self.service = "vacuum_clean_segment"
        elif "zone" in self.service_data:
            # "xiaomi_miio", "dreame_vacuum", "roborock"
            if self.domain == "xiaomi_miio":
                self.service_data.setdefault("repeats", 1)
            self.service = "vacuum_clean_zone"
        elif "x_coord" in self.service_data and "y_coord" in self.service_data:
            # "xiaomi_miio", "roborock"
            self.service = "vacuum_goto"

    async def internal_start(self, context: Context) -> None:
        self._attr_activity = VacuumActivity.CLEANING
        self.async_write_ha_state()

        if self.script:
            await self.script.async_run(context=context)

        if self.service:
            await self.hass.services.async_call(
                self.domain, self.service, self.service_data, True
            )

    async def internal_stop(self):
        self._attr_activity = VacuumActivity.IDLE
        self.async_write_ha_state()

    async def async_start(self):
        self.queue.append(self)

        state = self.hass.states.get(self.vacuum_entity_id)
        if len(self.queue) > 1 or state == VacuumActivity.CLEANING:
            self._attr_activity = VacuumActivity.PAUSED
            self.async_write_ha_state()
            return

        await self.internal_start(self._context)

    async def async_stop(self, **kwargs):
        for vacuum in self.queue:
            await vacuum.internal_stop()

        self.queue.clear()

        await self.internal_stop()
