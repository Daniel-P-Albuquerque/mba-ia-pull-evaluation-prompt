"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import (
    load_yaml,
    check_env_vars,
    print_section_header,
    validate_prompt_structure,
)

load_dotenv()


LOCAL_V2_PATH = "prompts/bug_to_user_story_v2.yml"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome curto do prompt (ex: 'bug_to_user_story_v2')
        prompt_data: Dados do prompt (dicionário interno do YAML)

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB não configurada no .env")
        return False

    full_name = f"{username}/{prompt_name}"

    system_prompt = prompt_data.get("system_prompt", "")
    user_prompt = prompt_data.get("user_prompt", "{bug_report}")

    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )

    techniques = prompt_data.get("techniques_applied", [])
    base_tags = prompt_data.get("tags", [])
    technique_tags = [f"technique:{t}" for t in techniques]
    all_tags = list(dict.fromkeys(base_tags + technique_tags))  # dedupe, preserva ordem

    description = prompt_data.get("description", "")
    if techniques:
        description = f"{description}\n\nTécnicas aplicadas: {', '.join(techniques)}".strip()

    try:
        client = Client()
        url = client.push_prompt(
            full_name,
            object=template,
            is_public=True,
            description=description,
            tags=all_tags,
        )
    except Exception as e:
        print(f"❌ Falha no push de '{full_name}': {e}")
        return False

    print(f"✓ Prompt publicado: {full_name}")
    print(f"   URL: {url}")
    print(f"   Tags: {all_tags}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def main() -> int:
    print_section_header("Push de Prompts ao LangSmith")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(LOCAL_V2_PATH)
    if not data:
        print(f"❌ Não foi possível carregar {LOCAL_V2_PATH}")
        return 1

    all_ok = True
    for prompt_name, prompt_data in data.items():
        if not isinstance(prompt_data, dict):
            continue

        print(f"\n→ Validando '{prompt_name}'...")
        is_valid, errors = validate_prompt(prompt_data)
        if not is_valid:
            print(f"❌ Validação falhou para '{prompt_name}':")
            for err in errors:
                print(f"   - {err}")
            all_ok = False
            continue
        print("   ✓ Validação OK")

        if not push_prompt_to_langsmith(prompt_name, prompt_data):
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
