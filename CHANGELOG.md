* 2024-05-25: v0.1.2 - Trigger Mechanism & Architecture Cleanup (Hannibal)  
  * Added `enable_trigger` and `trigger` (default `:>`) Valves to conditionally activate EasyTerm.
  * Completely removed `UserValves` and override logic to streamline the architecture for future expansions.
  * Added early-exit logic in `inlet` when the trigger condition is not met.
  * Maintained "Airy" formatting and extended debug logs for the trigger pipeline.

* 2024-05-25: v0.1.1 - Refactoring, Context Bypass & Debugging (Hannibal)  
  * Extracted `formatting_rules` to a global constant for cleaner code architecture.
  * Implemented `debug` configuration via Valves/UserValves with full logging support.
  * Added `bypass_context` feature to isolate the current command and prevent LLM Context Contamination.
  * Built a state-stash mechanism to save context in `inlet` and gracefully restore it in `outlet`.
  * Elevated Filter `__priority__` to 999999 to ensure it processes last in the OWUI pipeline.
  * Applied full 'Airy' code formatting and comprehensive docstrings.

* 2024-05-24: v0.1.0 - First Release