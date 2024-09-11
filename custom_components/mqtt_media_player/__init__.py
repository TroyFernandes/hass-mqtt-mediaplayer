from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the integration using YAML (if needed)."""
    return True  # Allow UI-only configuration

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from the UI."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of the integration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
