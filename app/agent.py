import asyncio
import json
from urllib.request import Request, urlopen

from mcp import Client
from mcp_server.server import mcp


def ask_model(messages, tools=None):
    payload = {
        "model": "qwen3:4b-instruct",
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0,
            "num_ctx": 4096,
            "num_predict": 500,
        },
    }

    if tools:
        payload["tools"] = tools

    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=180) as response:
        result = json.load(response)

    if result.get("done_reason") == "length":
        raise RuntimeError("Model response reached its output limit.")

    return result["message"]


async def main():
    question = input("Ask PolicyGuard Agent: ").strip()

    if not question:
        return

    async with Client(mcp) as client:
        available = await client.list_tools()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
            for tool in available.tools
            if tool.name == "get_resource_configuration"
        ]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are PolicyGuard. Use the configuration tool "
                    "when asked to inspect a fictional resource. "
                    "Never invent resource settings. "
                    "Report the returned facts concisely. "
                    "No policy documents are available in this test. "
                    "You cannot modify resources."
                ),
            },
            {"role": "user", "content": question},
        ]

        message = await asyncio.to_thread(
            ask_model, messages, tools
        )
        calls = message.get("tool_calls") or []

        if not calls:
            print("\nNo tool call was requested.")
            print(message.get("content", ""))
            return

        if len(calls) != 1:
            raise RuntimeError("This test permits one tool call only.")

        function = calls[0]["function"]
        name = function["name"]
        arguments = function["arguments"]

        if name != "get_resource_configuration":
            raise RuntimeError("Tool not permitted.")

        if (
            not isinstance(arguments, dict)
            or set(arguments) != {"resource_id"}
            or not isinstance(arguments["resource_id"], str)
        ):
            raise RuntimeError("Invalid tool arguments.")

        print(f"\nTool requested: {name}")
        print(f"Arguments: {json.dumps(arguments)}")

        result = await client.call_tool(name, arguments)

        if result.is_error:
            raise RuntimeError("MCP tool returned an error.")

        tool_text = "\n".join(
            block.text
            for block in result.content
            if block.type == "text"
        )

        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_name": name,
            "content": tool_text,
        })

        answer = await asyncio.to_thread(ask_model, messages)

        print("\nPolicyGuard:")
        print(answer.get("content", ""))


if __name__ == "__main__":
    asyncio.run(main())
