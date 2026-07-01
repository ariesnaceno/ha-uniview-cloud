"""Config flow for Uniview Cloud."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_API_BASE_URL,
    CONF_REGION,
    DEFAULT_API_BASE_URL,
    DEFAULT_REGION,
    DOMAIN,
)


class UniviewCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Uniview Cloud config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Uniview Cloud ({user_input[CONF_USERNAME]})",
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_REGION, default=DEFAULT_REGION): str,
                vol.Optional(CONF_API_BASE_URL, default=DEFAULT_API_BASE_URL): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
