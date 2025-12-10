import json
import os
import sys
import types

MOCK_DEPENDENCIES = os.getenv("MOCK_DEPENDENCIES") == "1" or "--mock-dependencies" in sys.argv
OFFLINE_GENERATION = False


def _coerce_text_from_message_content(content) -> str:
    if isinstance(content, list):
        collected = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                collected.append(str(item.get("text", "")))
            else:
                collected.append(str(item))
        return " ".join(collected)

    return str(content)


def _offline_llm_content(msg: str, system_message: str | None = None) -> str:
    text = _coerce_text_from_message_content(msg)
    if "NEW IDEA JSON" in text or (
        "\"Name\"" in text and "\"Experiment\"" in text and "\"Novelty\"" in text
    ):
        return (
            "THOUGHT: Proposing a feasible plan derived from the provided instructions. I am done.\n"
            "NEW IDEA JSON:\n" "```json\n"
            "{\"Name\": \"offline_plan\", \"Title\": \"Offline idea synthesized from prompt\", "
            "\"Experiment\": \"Implement the described plan with available code, logging key observations offline\", "
            "\"Interestingness\": 6, \"Feasibility\": 9, \"Novelty\": 5}"
            "\n```"
        )

    if "RESPONSE:" in text and "Query" in text:
        return _mock_llm_content(text)

    summary = text.strip().split("\n")[:4]
    joined = " ".join(line.strip() for line in summary if line.strip())
    if system_message:
        joined = f"System context: {system_message}. User prompt: {joined}"

    return (
        "THOUGHT: Generating an offline approximation of the requested completion.\n"
        f"RESPONSE: {joined if joined else text[:200]}"
    )


def _offline_llm_contents_from_messages(messages, n: int = 1):
    system_message = None
    user_message = None
    for msg in messages:
        if msg.get("role") == "system" and system_message is None:
            system_message = _coerce_text_from_message_content(msg.get("content", ""))
        if msg.get("role") == "user":
            user_message = _coerce_text_from_message_content(msg.get("content", ""))

    return [
        _offline_llm_content(user_message or "", system_message=system_message)
        for _ in range(max(n, 1))
    ]

if MOCK_DEPENDENCIES:
    def _identity_decorator(*args, **kwargs):  # pragma: no cover - compatibility shim
        def wrapper(func):
            return func

        return wrapper

    backoff = types.SimpleNamespace(on_exception=_identity_decorator, expo=lambda *args, **kwargs: None)

    class _DummyCompletions:
        def create(self, **kwargs):  # pragma: no cover - import-time shim
            raise RuntimeError("Mock LLM completions should be provided by the mock model path")

    class _DummyChat:
        def __init__(self):
            self.completions = _DummyCompletions()

    class _DummyClient:
        def __init__(self, *args, **kwargs):
            self.chat = _DummyChat()

    openai = types.SimpleNamespace(
        OpenAI=_DummyClient,
        RateLimitError=Exception,
        APITimeoutError=Exception,
    )
else:
    try:  # pragma: no cover - exercised in integration runs
        import backoff
        import openai
    except ImportError:  # pragma: no cover - offline fallback
        OFFLINE_GENERATION = True

        def _identity_decorator(*args, **kwargs):
            def wrapper(func):
                return func

            return wrapper

        backoff = types.SimpleNamespace(
            on_exception=_identity_decorator, expo=lambda *args, **kwargs: None
        )

        class _OfflineChoice:
            def __init__(self, content):
                self.message = types.SimpleNamespace(content=content)

        class _OfflineCompletions:
            def create(self, **kwargs):  # pragma: no cover - shim
                contents = _offline_llm_contents_from_messages(
                    kwargs.get("messages", []), n=kwargs.get("n", 1)
                )
                return types.SimpleNamespace(
                    choices=[_OfflineChoice(c) for c in contents]
                )

        class _OfflineChat:
            def __init__(self):
                self.completions = _OfflineCompletions()

        class _OfflineMessageContent:
            def __init__(self, text):
                self.text = text

        class _OfflineMessages:
            def create(self, **kwargs):
                messages = kwargs.get("messages", [])
                contents = _offline_llm_contents_from_messages(messages)
                return types.SimpleNamespace(
                    content=[_OfflineMessageContent(c) for c in contents]
                )

        class _OfflineClient:
            def __init__(self, *args, **kwargs):
                self.chat = _OfflineChat()
                self.messages = _OfflineMessages()

        openai = types.SimpleNamespace(
            OpenAI=_OfflineClient,
            RateLimitError=Exception,
            APITimeoutError=Exception,
        )
    else:
        OFFLINE_GENERATION = False


# Get N responses from a single message, used for ensembling.
@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError))
def get_batch_responses_from_llm(
    msg,
    client,
    model,
    system_message,
    print_debug=False,
    msg_history=None,
    temperature=0.75,
    n_responses=1,
):
    if msg_history is None:
        msg_history = []

    offline_mode = (MOCK_DEPENDENCIES or OFFLINE_GENERATION) and isinstance(
        client, openai.OpenAI
    )

    if model == "mock-llm":
        content = [_mock_llm_content(msg) for _ in range(n_responses)]
        new_msg_history = [
            msg_history
            + [
                {"role": "user", "content": msg},
                {"role": "assistant", "content": c},
            ]
            for c in content
        ]
    elif offline_mode and model in [
        "gpt-4o-2024-05-13",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
    ]:
        content = [_offline_llm_content(msg, system_message) for _ in range(n_responses)]
        new_msg_history = [
            msg_history
            + [
                {"role": "user", "content": msg},
                {"role": "assistant", "content": c},
            ]
            for c in content
        ]
    elif model in [
        "gpt-4o-2024-05-13",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
    ]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=3000,
            n=n_responses,
            stop=None,
            seed=0,
        )
        content = [r.message.content for r in response.choices]
        new_msg_history = [
            new_msg_history + [{"role": "assistant", "content": c}] for c in content
        ]
    elif model == "deepseek-coder-v2-0724":
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=3000,
            n=n_responses,
            stop=None,
        )
        content = [r.message.content for r in response.choices]
        new_msg_history = [
            new_msg_history + [{"role": "assistant", "content": c}] for c in content
        ]
    elif model == "llama-3-1-405b-instruct":
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-405b-instruct",
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=3000,
            n=n_responses,
            stop=None,
        )
        content = [r.message.content for r in response.choices]
        new_msg_history = [
            new_msg_history + [{"role": "assistant", "content": c}] for c in content
        ]
    elif model == "claude-3-5-sonnet-20240620":
        content, new_msg_history = [], []
        for _ in range(n_responses):
            c, hist = get_response_from_llm(
                msg,
                client,
                model,
                system_message,
                print_debug=False,
                msg_history=None,
                temperature=temperature,
            )
            content.append(c)
            new_msg_history.append(hist)
    else:
        # TODO: This is only supported for GPT-4 in our reviewer pipeline.
        raise ValueError(f"Model {model} not supported.")

    if print_debug:
        # Just print the first one.
        print()
        print("*" * 20 + " LLM START " + "*" * 20)
        for j, msg in enumerate(new_msg_history[0]):
            print(f'{j}, {msg["role"]}: {msg["content"]}')
        print(content)
        print("*" * 21 + " LLM END " + "*" * 21)
        print()

    return content, new_msg_history


@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError))
def get_response_from_llm(
    msg,
    client,
    model,
    system_message,
    print_debug=False,
    msg_history=None,
    temperature=0.75,
):
    if msg_history is None:
        msg_history = []

    offline_mode = (MOCK_DEPENDENCIES or OFFLINE_GENERATION) and isinstance(
        client, openai.OpenAI
    )

    if model == "mock-llm":
        content = _mock_llm_content(msg)
        new_msg_history = msg_history + [
            {"role": "user", "content": msg},
            {"role": "assistant", "content": content},
        ]
    elif offline_mode and model in [
        "gpt-4o-2024-05-13",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
    ]:
        content = _offline_llm_content(msg, system_message)
        new_msg_history = msg_history + [
            {"role": "user", "content": msg},
            {"role": "assistant", "content": content},
        ]
    elif model == "claude-3-5-sonnet-20240620":
        new_msg_history = msg_history + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": msg,
                    }
                ],
            }
        ]
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=3000,
            temperature=temperature,
            system=system_message,
            messages=new_msg_history,
        )
        content = response.content[0].text
        new_msg_history = new_msg_history + [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": content,
                    }
                ],
            }
        ]
    elif model in [
        "gpt-4o-2024-05-13",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
    ]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=3000,
            n=1,
            stop=None,
            seed=0,
        )
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model == "deepseek-coder-v2-0724":
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=3000,
            n=1,
            stop=None,
        )
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model in ["meta-llama/llama-3.1-405b-instruct", "llama-3-1-405b-instruct"]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-405b-instruct",
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=3000,
            n=1,
            stop=None,
        )
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    else:
        raise ValueError(f"Model {model} not supported.")

    if print_debug:
        print()
        print("*" * 20 + " LLM START " + "*" * 20)
        for j, msg in enumerate(new_msg_history):
            print(f'{j}, {msg["role"]}: {msg["content"]}')
        print(content)
        print("*" * 21 + " LLM END " + "*" * 21)
        print()

    return content, new_msg_history


def extract_json_between_markers(llm_output):
    json_start_marker = "```json"
    json_end_marker = "```"

    # Find the start and end indices of the JSON string
    start_index = llm_output.find(json_start_marker)
    if start_index != -1:
        start_index += len(json_start_marker)  # Move past the marker
        end_index = llm_output.find(json_end_marker, start_index)
    else:
        return None  # JSON markers not found

    if end_index == -1:
        return None  # End marker not found

    # Extract the JSON string
    json_string = llm_output[start_index:end_index].strip()
    try:
        parsed_json = json.loads(json_string)
        return parsed_json
    except json.JSONDecodeError:
        return None  # Invalid JSON format


def _mock_llm_content(msg: str) -> str:
    if "RESPONSE:" in msg and "Query" in msg:
        return (
            "THOUGHT: Conducted quick survey. Decision made: novel.\n"
            "RESPONSE:\n````json\n{\"Query\": \"mock topic exploration\"}\n````"
        ).replace("````", "```")

    return (
        "THOUGHT: Drafting a placeholder idea for offline testing. I am done.\n"
        "NEW IDEA JSON:\n```json\n"
        "{\"Name\": \"mock_idea\", \"Title\": \"Mock research idea\", "
        "\"Experiment\": \"Run unit tests with fake data\", "
        "\"Interestingness\": 5, \"Feasibility\": 10, \"Novelty\": 6}"
        "\n```"
    )
