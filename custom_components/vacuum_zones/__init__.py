import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_ENTITY_ID, CONF_SEQUENCE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

DOMAIN = "vacuum_zones"
PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ENTITY_ID): cv.entity_id,
                vol.Required("zones"): {
                    cv.string: vol.Schema(
                        {
                            vol.Optional("name"): str,
                            vol.Optional("unique_id"): str,
                            vol.Optional("room"): vol.Any(list, int),
                            vol.Optional("zone"): list,
                            vol.Optional("repeats"): int,
                            vol.Optional("goto"): list,
                            vol.Optional(CONF_SEQUENCE): cv.SCRIPT_SCHEMA,
                        },
                        extra=vol.ALLOW_EXTRA,
                    )
                },
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    hass.async_create_task(
        async_load_platform(hass, "vacuum", DOMAIN, config[DOMAIN], config)
    )
    return True
