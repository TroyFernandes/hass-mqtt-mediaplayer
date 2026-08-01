import voluptuous as vol
from homeassistant import config_entries

from homeassistant.const import CONF_NAME
from .const import DOMAIN

@config_entries.HANDLERS.register(DOMAIN)
class MqttMediaPlayerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_mqtt(self, discovery_info=None):
        """Handle MQTT discovery."""
        if discovery_info is None:
            return self.async_abort(reason="no_discovery_info")

        device_name = discovery_info.get("name", "MQTT Media Player")
        
        # Check if already configured
        await self.async_set_unique_id(device_name)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=device_name,
            data=discovery_info
        )

    async def async_step_user(self, user_input=None):
        """Handle manual configuration attempts."""
        return self.async_abort(reason="mqtt_discovery_only")