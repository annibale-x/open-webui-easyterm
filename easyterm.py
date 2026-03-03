"""
title: 🖥️ EasyTerm
version: 0.1.1
author: Hannibal
repository: https://github.com/annibale-x/open-webui-easyterm
author_email: annibale.x@gmail.com
author_url: https://openwebui.com/u/h4nn1b4l
description: Mandates full command completion for OpenTerminal and forces clean formatting.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Extracting formatting rules into a global constant to keep Valves clean
FORMATTING_RULES = """
- MODE: STRICT API PASSTHROUGH.
- ANTI-RAG DIRECTIVE: The context contains raw tool output, NOT a search document. DO NOT treat this as a RAG query. DO NOT summarize the processes. DO NOT cite sources (e.g., avoid using [1]). DO NOT use bullet points.
- INSTRUCTION: Concatenate the fragmented `data` strings from the JSON into a single text block.
- FORMAT: Output the exact merged text inside one single ```bash block. 
- RULE: Zero conversational text. No preamble, no postamble. Just the code block.
"""


class Filter:
    """
    Main filter class for EasyTerm.
    Handles context truncation, prompt injection, and OpenTerminal formatting enforcement.
    """

    __priority__ = 999999

    class Valves(BaseModel):
        """
        Global configurations for EasyTerm.
        """

        max_command_wait: int = Field(
            default=60,
            description="Global maximum wait time (in seconds) for OpenTerminal commands.",
        )
        debug: bool = Field(
            default=False,
            description="Enable debug logging and payload dumps.",
        )
        bypass_context: bool = Field(
            default=False,
            description="If True, sends ONLY the current message to the LLM, preventing context contamination.",
        )

    class UserValves(BaseModel):
        """
        User-specific configurations. Overrides global Valves when set.
        """

        max_command_wait: Optional[int] = Field(
            default=30,
            description="Override the global maximum wait time (in seconds) for your OpenTerminal commands. Leave empty to use the global default.",
        )
        debug: Optional[bool] = Field(
            default=False,
            description="Override global debug preference.",
        )
        bypass_context: Optional[bool] = Field(
            default=False,
            description="Override global context bypass preference.",
        )

    def __init__(self):
        """
        Initializes the Filter with default valves and a state stash for context restoration.
        """

        self.valves = self.Valves()
        self._message_stash = {}

    def _get_override(self, user_valves, key: str, default_value):
        """
        Safely retrieves a configuration value, prioritizing UserValves over global Valves.
        """

        if user_valves and hasattr(user_valves, key):
            val = getattr(user_valves, key)

            if val is not None:
                return val

        return default_value

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Intercepts the request, applying context bypass, logging, and prompt injection.
        """

        terminal_id = body.get("terminal_id")

        if not terminal_id:
            return body

        messages = body.get("messages", [])

        if not messages:
            return body

        user_valves = __user__.get("valves") if __user__ else None
        wait_time = self._get_override(
            user_valves, "max_command_wait", self.valves.max_command_wait
        )
        debug_mode = self._get_override(user_valves, "debug", self.valves.debug)
        bypass_ctx = self._get_override(
            user_valves, "bypass_context", self.valves.bypass_context
        )

        if debug_mode:
            logger.debug(
                f"[EasyTerm] Inlet triggered. wait_time={wait_time}, bypass_context={bypass_ctx}"
            )

        if bypass_ctx:
            user_id = __user__.get("id", "anonymous") if __user__ else "anonymous"
            self._message_stash[user_id] = messages.copy()
            isolated_messages = [messages[-1]]
            messages = isolated_messages
            body["messages"] = messages

            if debug_mode:
                logger.debug(
                    f"[EasyTerm] Context bypassed. Stashed {len(self._message_stash[user_id])} messages for user {user_id}."
                )

        dynamic_rule_wait = (
            f"- MANDATORY WAIT PARAMETER: You MUST inject the integer value {wait_time} into the `wait` parameter of your JSON payload.\n"
            f"  NEVER use null, NEVER leave it empty.\n"
            f"  Example:\n"
            f"  {{\n"
            f'     "command": "<your_command>",\n'
            f'     "wait": {wait_time}\n'
            f"  }}"
        )

        injected_prompt = (
            f"\n\n<PROTOCOL FOR OpenTerminal>\n"
            f"If you are using the OpenTerminal for this task, you MUST adhere to the following rules:\n"
            f"{dynamic_rule_wait}\n"
            f"{FORMATTING_RULES}\n"
            f"</PROTOCOL>\n"
        )

        for message in reversed(messages):

            if message["role"] == "user":
                message["content"] += injected_prompt

                if debug_mode:
                    logger.debug(
                        f"[EasyTerm] Prompt injected into user message. Dump:\n{injected_prompt}"
                    )

                break

        return body

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Intercepts the response. Restores the original context if bypass_context was active.
        """

        user_valves = __user__.get("valves") if __user__ else None
        debug_mode = self._get_override(user_valves, "debug", self.valves.debug)
        bypass_ctx = self._get_override(
            user_valves, "bypass_context", self.valves.bypass_context
        )

        if debug_mode:
            logger.debug("[EasyTerm] Outlet triggered.")

        if bypass_ctx:
            user_id = __user__.get("id", "anonymous") if __user__ else "anonymous"

            if user_id in self._message_stash:
                original_messages = self._message_stash.pop(user_id)
                body["messages"] = original_messages

                if debug_mode:
                    logger.debug(
                        f"[EasyTerm] Context restored for user {user_id}. Restored {len(original_messages)} messages."
                    )

        return body
