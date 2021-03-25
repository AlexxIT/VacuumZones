from typing import List

from homeassistant.components.vacuum import StateVacuumEntity, SUPPORT_START, \
    SUPPORT_STOP, DOMAIN as VACUUM_DOMAIN, STATE_CLEANING, STATE_RETURNING, \
    STATE_DOCKED
from homeassistant.const import CONF_SEQUENCE, STATE_IDLE, STATE_PAUSED, \
    EVENT_STATE_CHANGED, ATTR_ENTITY_ID
from homeassistant.core import Event, State
from homeassistant.helpers.script import Script


async def async_setup_platform(hass, _, async_add_entities,
                               discovery_info=None):
    entity_id = discovery_info['entity_id']
    queue: List[XiaomiVacuum] = []
    entities = [
        XiaomiVacuum(name, config, entity_id, queue)
        for name, config in discovery_info['zones'].items()
    ]
    async_add_entities(entities)

    async def state_changed_event_listener(event: Event):
        if entity_id != event.data.get(ATTR_ENTITY_ID) or not queue:
            return

        new_state: State = event.data.get('new_state')
        if new_state.state not in (STATE_RETURNING, STATE_DOCKED):
            return

        prev: XiaomiVacuum = queue.pop(0)
        await prev.internal_stop()

        if not queue:
            return

        next_: XiaomiVacuum = queue[0]
        await next_.internal_start()

    hass.bus.async_listen(EVENT_STATE_CHANGED, state_changed_event_listener)


class XiaomiVacuum(StateVacuumEntity):
    _state = STATE_IDLE
    script = None

    def __init__(self, name: str, config: dict, entity_id: str, queue: list):
        config['name'] = name
        config['entity_id'] = entity_id
        self.config = config
        self.queue = queue

    async def async_added_to_hass(self):
        if CONF_SEQUENCE in self.config:
            self.script = Script(self.hass, self.config[CONF_SEQUENCE],
                                 self.name, VACUUM_DOMAIN)

    @property
    def name(self):
        return self.config['name']

    @property
    def state(self):
        return self._state

    @property
    def supported_features(self):
        return SUPPORT_START | SUPPORT_STOP

    async def internal_start(self):
        self._state = STATE_CLEANING
        await self.async_update_ha_state()

        if self.script:
            await self.script.async_run()

        if 'room' in self.config:
            await self.hass.services.async_call(
                'xiaomi_miio', 'vacuum_clean_segment', {
                    'entity_id': self.config['entity_id'],
                    'segments': self.config['room'],
                }, blocking=True)

        elif 'zone' in self.config:
            await self.hass.services.async_call(
                'xiaomi_miio', 'vacuum_clean_zone', {
                    'entity_id': self.config['entity_id'],
                    'zone': self.config['zone'],
                    'repeats': self.config.get('repeats', 1)
                }, blocking=True)

        elif 'goto' in self.config:
            await self.hass.services.async_call(
                'xiaomi_miio', 'vacuum_goto', {
                    'entity_id': self.config['entity_id'],
                    'x_coord': self.config['goto'][0],
                    'y_coord': self.config['goto'][1],
                }, blocking=True)

    async def internal_stop(self):
        self._state = STATE_IDLE
        await self.async_update_ha_state()

    async def async_start(self):
        self.queue.append(self)

        state = self.hass.states.get(self.config['entity_id'])
        if len(self.queue) > 1 or state == STATE_CLEANING:
            self._state = STATE_PAUSED
            await self.async_update_ha_state()
            return

        await self.internal_start()

    async def async_stop(self, **kwargs):
        for vacuum in self.queue:
            await vacuum.internal_stop()

        self.queue.clear()

        await self.internal_stop()
