## 🖥️ EasyTerm v0.1.2: Open-Terminal Formatting Filter

EasyTerm is an experimental filter designed for Open WebUI's newly released **Open-Terminal** tool. It explores prompt-engineering techniques to force conversational LLMs to behave as simple, headless terminal outputs, managing buffer aggregation and suppressing conversational filler.

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?logo=github&logoColor=white)](https://github.com/annibale-x/open-webui-easyterm)
![Open WebUI Plugin](https://img.shields.io/badge/Open%20WebUI-Filter-blue?style=flat&logo=openai)
![License](https://img.shields.io/github/license/annibale-x/open-webui-easyterm?color=green)

---

### ✨ Features

- **Headless Output:** Forces the LLM to return only raw terminal data inside a `bash` code block, bypassing its default behavior to add preambles, summaries, or explanations.
- **Buffer Aggregation:** Concatenates fragmented JSON `data` strings (common in asynchronous terminal outputs like `top` or `ps`) into a single text block before rendering.
- **Context Bypass:** Temporarily stashes chat history during command execution, sending only the current command to the LLM. This prevents smaller models (8B-14B) from getting confused by previous terminal outputs.
- **Parameter Enforcement:** Injects strict rules to prevent type-inference failures (e.g., `wait: null`) in certain models when calling the Open-Terminal tool.

---

### 🔧 Configuration (Valves)

| Valve | Default | Description |
| :--- | :---: | :--- |
| **Enable Trigger** | `False` | Only activates EasyTerm when the user message starts with the defined trigger. |
| **Trigger** | `:>` | The required prefix if `Enable Trigger` is active. |
| **Bypass Context** | `False` | Sends only the current message to the LLM to prevent context drift. |
| **Max Command Wait** | `60` | Fallback integer injected into the tool's `wait` parameter. |
| **Priority** | `999999` | Sets the filter's execution priority (higher values run last). |
| **Debug Mode** | `False` | Enables backend logging for context stash and prompt injection monitoring. |

---

### 🛠️ Technical Details

- **Anti-RAG Override:** Open WebUI typically injects tool results with citations (e.g., `[1]`), which triggers a summarization response in micro models EasyTerm injects a directive to explicitly ignore these citations and treat the payload as a raw string.
- **Context Stashing:** To truncate the LLM context without permanently deleting chat history, the `inlet` function backs up `body["messages"]` to a local dictionary, passes a single message to the API, and the `outlet` function restores the original UI state.
- **Persona Anchoring:** Uses Zero-Shot prompting to assign a "Terminal Console" role to the model, limiting its syntactic output to raw data streams.

---

### 🚧 Roadmap: v0.2.0

While the current version focuses on plain text block rendering, future experiments will explore structured parsing:
- **Markdown Tables:** Parsing columnar data (e.g., `df -h`) into native Markdown tables.
- **Syntax Highlighting:** Automatic language detection based on file extensions for `cat` or `tail` commands.
- **Metadata Separation:** Splitting system headers (like CPU/RAM stats) from raw data grids.

---

### 🐞 Support

Tested against: Llama 3.1, Phi4, Gemma 3, DeepSeek, Cogito, Gpt-Oss, Gemini 1.5 Flash, GPT-4o-Mini, and Qwen. 
If a specific model architecture fails to follow the formatting directives, please open an issue on [GitHub](https://github.com/annibale-x/open-webui-easyterm/issues).