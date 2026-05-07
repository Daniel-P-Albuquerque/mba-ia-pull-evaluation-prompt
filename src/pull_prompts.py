"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


PROMPT_HUB_REF = "leonanluppi/bug_to_user_story_v1"
LOCAL_PATH = "prompts/bug_to_user_story_v1.yml"
TOP_LEVEL_KEY = "bug_to_user_story_v1"


def _extract_template(message) -> str:
    """Recupera o texto de template de uma message do ChatPromptTemplate."""
    prompt_obj = getattr(message, "prompt", None)
    if prompt_obj is not None and hasattr(prompt_obj, "template"):
        return prompt_obj.template
    if hasattr(message, "template"):
        return message.template
    if hasattr(message, "content"):
        return message.content
    return str(message)


def _classify(message) -> str:
    """Retorna 'system', 'user' ou 'other' a partir do tipo da message."""
    name = type(message).__name__.lower()
    if "system" in name:
        return "system"
    if "human" in name or "user" in name:
        return "user"
    return "other"


def pull_prompts_from_langsmith() -> bool:
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    print(f"Puxando prompt: {PROMPT_HUB_REF}")
    try:
        prompt = hub.pull(PROMPT_HUB_REF)
    except Exception as e:
        print(f"❌ Falha ao puxar do Hub: {e}")
        print("   Verifique LANGSMITH_API_KEY, conexão com a internet e o nome do prompt.")
        return False

    messages = getattr(prompt, "messages", None)
    if not messages:
        print("❌ Prompt retornado não contém messages — formato inesperado.")
        return False

    system_prompt = ""
    user_prompt = ""
    for msg in messages:
        kind = _classify(msg)
        template = _extract_template(msg)
        if kind == "system":
            system_prompt = template
        elif kind == "user":
            user_prompt = template

    if not system_prompt and not user_prompt:
        print("❌ Não foi possível extrair templates de system/user do prompt.")
        return False

    data = {
        TOP_LEVEL_KEY: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt or "{bug_report}",
            "version": "v1",
            "created_at": date.today().isoformat(),
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if not save_yaml(data, LOCAL_PATH):
        return False

    print(f"✓ Prompt salvo em {LOCAL_PATH}")
    return True


def main() -> int:
    print_section_header("Pull de Prompts do LangSmith")
    return 0 if pull_prompts_from_langsmith() else 1


if __name__ == "__main__":
    sys.exit(main())
