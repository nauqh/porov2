import json
from openai import OpenAI
from loguru import logger

from tools import (
    fetch_all_code_from_repo,
    search_db,
    extract_owner,
    extract_repo,
    get_ta_role_for_forum,
    search_youtube
)


class Assistant:
    def __init__(
        self,
        session_id: str,
        model: str = "gpt-4.1",
        tool_schema_path: str = "tool_schemas.json",
        instructions_path: str = "instructions.txt"
    ):
        self.client = OpenAI()
        self.session_id = session_id
        self.model = model

        # Load tools and instructions
        with open(tool_schema_path, 'r', encoding='utf-8') as f:
            self.tools = json.load(f)
        with open(instructions_path, 'r', encoding='utf-8') as f:
            instr = f.read().strip()

        self.history = [{"role": "system", "content": instr}]
        self.previous_response_id = None

        # Tool dispatcher
        self.tool_dispatch = {
            fn.__name__: fn for fn in (
                get_ta_role_for_forum,
                extract_owner,
                extract_repo,
                fetch_all_code_from_repo,
                search_db,
                search_youtube,
            )
        }

    def call_function(self, name: str, arguments: dict) -> str:
        logger.info(
            f"[{self.session_id}] Calling function: {name} args: {arguments}")
        fn = self.tool_dispatch.get(name)
        if not fn:
            return f"No implementation for '{name}'"
        result = fn(**arguments)
        return json.dumps(result) if not isinstance(result, str) else result

    def ask(self, text: str) -> str:
        self.history.append({"role": "user", "content": text})

        while True:
            resp = self.client.responses.create(
                model=self.model,
                input=self.history,
                tools=self.tools,
                previous_response_id=self.previous_response_id,
                parallel_tool_calls=True,
                user=self.session_id
            )
            self.previous_response_id = resp.id

            calls = [call for call in resp.output if call.type == 'function_call']
            if not calls:
                self.history += [
                    {"role": output.role, "content": output.content} for output in resp.output
                ]
                return resp.output_text

            for call in calls:
                args = json.loads(call.arguments)
                out = self.call_function(call.name, args)
                self.history.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": out
                })


class ConversationManager:
    def __init__(self):
        self.sessions: dict[str, Assistant] = {}

    def get_bot(self, conv_id: str) -> Assistant:
        if conv_id not in self.sessions:
            self.sessions[conv_id] = Assistant(conv_id)
        return self.sessions[conv_id]

    def handle_message(self, conv_id: str, text: str) -> str:
        return self.get_bot(conv_id).ask(text)

    def end_conversation(self, conv_id: str):
        self.sessions.pop(conv_id, None)


if __name__ == '__main__':
    mgr = ConversationManager()
    print("Usage: conv_id Your text here")

    while True:
        line = input().strip()
        if not line:
            break

        parts = line.split()
        conv_id = parts[0]

        if conv_id == 'reset' and len(parts) == 2:
            mgr.end_conversation(parts[1])
            print(f"Session '{parts[1]}' reset.")
            continue

        text = ' '.join(parts[1:])
        print("Text:", text)

        reply = mgr.handle_message(conv_id, text)
        print(f"[{conv_id}] {reply}")
