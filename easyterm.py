"""
title: 🖥️ EasyTerm
version: 0.1.2
author: Hannibal
repository: https://github.com/annibale-x/open-webui-easyterm
author_email: annibale.x@gmail.com
author_url: https://openwebui.com/u/h4nn1b4l
description: Mandates full command completion for OpenTerminal and forces clean output.
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
- FORMAT: Output the exact merged text inside exactly one Markdown code block. You MUST use the exact syntax tag ```bash to open the block. NEVER use plain ``` .
- RULE: Zero conversational text. No preamble, no postamble. Just the code block and IMMEDIATLY END THE TASK.
"""


class Filter:
    """
    Main filter class for EasyTerm.
    Handles context truncation, prompt injection, and OpenTerminal formatting enforcement.
    """

    class Valves(BaseModel):
        """
        Global configurations for EasyTerm.
        """

        enable_trigger: bool = Field(
            default=False,
            description="If True, EasyTerm will only activate when the user's message starts with the trigger.",
        )
        trigger: str = Field(
            default=":>",
            description="The prefix required to trigger EasyTerm if enable_trigger is True.",
        )
        max_command_wait: int = Field(
            default=60,
            description="Global maximum wait time (in seconds) for OpenTerminal commands.",
        )
        bypass_context: bool = Field(
            default=False,
            description="If True, sends ONLY the current message to the LLM, preventing context contamination.",
        )
        priority: int = Field(
            default=999999, 
            description="Filter priority"
        )
        debug: bool = Field(
            default=False,
            description="Enable debug logging and payload dumps.",
        )

    def __init__(self):
        """
        Initializes the Filter with default valves and a state stash for context restoration.
        """

        self.valves = self.Valves()
        self._message_stash = {}

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Intercepts the request, applying trigger checks, context bypass, logging, and prompt injection.
        """

        terminal_id = body.get("terminal_id")

        if not terminal_id:
            return body

        messages = body.get("messages", [])

        if not messages:
            return body

        last_message_content = messages[-1].get("content", "").strip()

        if self.valves.enable_trigger:

            if not last_message_content.startswith(self.valves.trigger):

                if self.valves.debug:
                    logger.debug(
                        f"[EasyTerm] Trigger '{self.valves.trigger}' not found in message. Skipping."
                    )

                return body

        wait_time = self.valves.max_command_wait
        debug_mode = self.valves.debug
        bypass_ctx = self.valves.bypass_context

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

        debug_mode = self.valves.debug
        bypass_ctx = self.valves.bypass_context

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
