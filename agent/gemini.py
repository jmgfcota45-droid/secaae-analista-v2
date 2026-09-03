
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from google import genai

from agent.prompts import SYSTEM_PROMPT
from agent.tools import FUNCTIONS, TOOL_DECLARATIONS
from data.database import Database


@dataclass
class AgentResponse:
    text: str
    interaction_id: str | None
    tool_calls: list[dict[str, Any]]


class GeminiAgent:
    def __init__(self, db: Database, api_key: str, model: str, max_rounds: int = 8):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY não configurada. Configure a variável de ambiente."
            )

        self.db = db
        self.model = model
        self.max_rounds = max_rounds
        self.client = genai.Client(api_key=api_key)

    def _system_instruction(self) -> str:
        schema = self.db.schema_context()
        return SYSTEM_PROMPT.format(schema_context=schema)

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        if name not in FUNCTIONS:
            raise ValueError(f"Ferramenta não autorizada: {name}")

        if name == "run_query":
            arguments = dict(arguments)
            arguments["max_rows"] = min(
                int(arguments.get("max_rows", 500)), 500
            )

        result = FUNCTIONS[name](self.db, **arguments)
        return result

    def ask(
        self,
        user_message: str,
        previous_interaction_id: str | None = None,
    ) -> AgentResponse:
        interaction_id = previous_interaction_id
        tool_calls_log: list[dict[str, Any]] = []

        if interaction_id:
            interaction = self.client.interactions.create(
                model=self.model,
                previous_interaction_id=interaction_id,
                input=user_message,
                tools=TOOL_DECLARATIONS,
                system_instruction=self._system_instruction(),
            )
        else:
            interaction = self.client.interactions.create(
                model=self.model,
                input=user_message,
                tools=TOOL_DECLARATIONS,
                system_instruction=self._system_instruction(),
            )

        for _round in range(self.max_rounds):
            calls = [
                step for step in interaction.steps
                if getattr(step, "type", None) == "function_call"
            ]

            if not calls:
                return AgentResponse(
                    text=interaction.output_text or "Não foi possível gerar uma resposta.",
                    interaction_id=interaction.id,
                    tool_calls=tool_calls_log,
                )

            function_inputs = []

            for call in calls:
                name = call.name
                arguments = dict(call.arguments or {})

                try:
                    result = self._execute_tool(name, arguments)
                    error = None
                except Exception as exc:
                    result = {
                        "error": f"{type(exc).__name__}: {exc}"
                    }
                    error = str(exc)

                tool_calls_log.append({
                    "name": name,
                    "arguments": arguments,
                    "error": error,
                })

                function_inputs.append({
                    "type": "function_result",
                    "name": name,
                    "call_id": call.id,
                    "result": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                result,
                                ensure_ascii=False,
                                default=str,
                            ),
                        }
                    ],
                })

            interaction = self.client.interactions.create(
                model=self.model,
                previous_interaction_id=interaction.id,
                input=function_inputs,
                tools=TOOL_DECLARATIONS,
                system_instruction=self._system_instruction(),
            )

        return AgentResponse(
            text=(
                "A análise atingiu o limite de etapas de consulta. "
                "Tente formular a pergunta de maneira mais específica."
            ),
            interaction_id=interaction.id,
            tool_calls=tool_calls_log,
        )
