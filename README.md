## 🖥️ EasyTerm v0.1.2: Advanced Open-Terminal Output Formatter

EasyTerm is a technical filter designed for the experimental **Open-Terminal** tool in Open WebUI. It standardizes terminal output formatting, manages asynchronous buffer aggregation, and mitigates conversational drift/hallucinations in LLMs by enforcing a headless execution environment.

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?logo=github&logoColor=white)](https://github.com/annibale-x/open-webui-easyterm)
![Open WebUI Plugin](https://img.shields.io/badge/Open%20WebUI-Filter-blue?style=flat&logo=openai)
![License](https://img.shields.io/github/license/annibale-x/open-webui-easyterm?color=green)

---

### ✨ Core Functionalities

- **Conversational Suppression:** Forces the LLM to act strictly as a headless terminal stdout. Suppresses preambles, summaries, and "helpful" explanations.
- **Asynchronous Buffer Aggregation:** Intercepts fragmented JSON `data` strings caused by OS buffer flushing (common in tools like `top` or `ps`) and concatenates them into a single contiguous block.
- **Context Isolation (Bypass):** Dynamically stashes chat history during command execution. The LLM receives only the current command and its raw output, preventing "Context Contamination" in smaller models (8B-14B).
- **Schema Enforcement:** Corrects type-inference failures in specific models (e.g., Gemma3) by forcing strict integer typing for tool parameters like `wait`.
- **Pipeline Priority:** Operates at priority `999999` to ensure it is the final interceptor in the `inlet` and `outlet` cycles.

---

### 🚀 Technical Use Cases

Open-Terminal is highly experimental. EasyTerm provides the necessary logic layer to make it production-ready across different LLM architectures.

#### 1. Headless Execution
Standard integrations often include conversational filler. EasyTerm ensures that a command like `cat /etc/os-release` returns **only** the raw file content within a single `bash` code block.

#### 2. Multi-Block Aggregation
For commands like `top -b -n 1`, Open-Terminal may return multiple JSON output blocks. EasyTerm instructs the LLM to aggregate these fragments before rendering, preventing broken or split code blocks.

#### 3. State Management (Context Bypass)
During long debugging sessions, history can pollute the prompt. When `bypass_context` is active, EasyTerm clears the history for the current API call and restores it once the response is received, ensuring 100% focus on the terminal data.

---

### 🔧 Configuration (Valves)

| Valve | Default | Description |
| :--- | :---: | :--- |
| **Enable Trigger** | `False` | Only activates EasyTerm when the user message starts with the defined trigger. |
| **Trigger** | `:>` | The required prefix (e.g., `:> ls -la`) if `Enable Trigger` is active. |
| **Bypass Context** | `False` | **Recommended for mini models.** Sends only the current message to the LLM to prevent context drift. |
| **Max Command Wait** | `60` | Fallback integer injected into the tool's `wait` parameter. |
| **Debug Mode** | `False` | Enables backend logging for context stash and prompt injection monitoring. |

---

### 🛠️ Implementation Details

#### Anti-RAG Interception
Open WebUI often injects tool results as documents (e.g., `[1] (Source: ...)`). This triggers a "summarization bias" in models like Llama 3.1. EasyTerm injects a specific directive to ignore citations and treat the payload strictly as a passthrough string.

#### Context Stashing Logic
To bypass context without losing chat history, EasyTerm implements a backup mechanism. During the `inlet` phase, it saves `body["messages"]` to a local dictionary keyed by `user_id`, sends only the last message to the LLM, and restores the original state during the `outlet` phase.

#### Headless Persona Enforcement
Anchors the model to a "Terminal Console" role. This Zero-Shot instruction defines a rigid syntactic limit: the model must treat its output as a pure data stream, suppressing closing notes or explanatory chatter.

---

### 🚧 Roadmap: v0.2.0 (Smart Parsing)

Work is underway to implement structural data enrichment:
- **Markdown Table Extraction:** Detection and parsing of columnar data (e.g., `df -h`) into native tables.
- **Dynamic Syntax Highlighting:** Automatic language detection based on file extensions during `cat`/`tail` operations.
- **Metadata Separation:** Extracting system headers (CPU/RAM stats) from raw data grids.

---

### 🐞 Support

Tested on: Llama 3.1, Phi4, Gemma 3, DeepSeek, Cogito, Gpt-Oss, Gemini 3 Flash, Gpt-4o-Mini  and Qwen. 
If a specific quantization or model architecture ignores the silence directives, please open an issue on [GitHub](https://github.com/annibale-x/open-webui-easyterm/issues).