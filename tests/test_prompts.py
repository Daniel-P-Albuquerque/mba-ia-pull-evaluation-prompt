"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    raw = load_prompts(str(PROMPT_PATH))
    assert raw is not None, f"YAML vazio ou inválido em {PROMPT_PATH}"
    assert PROMPT_KEY in raw, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
    return raw[PROMPT_KEY]


@pytest.fixture(scope="module")
def yaml_text():
    return PROMPT_PATH.read_text(encoding="utf-8")


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' ausente"
        system_prompt = prompt_data["system_prompt"]
        assert isinstance(system_prompt, str), "'system_prompt' deve ser string"
        assert system_prompt.strip(), "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        text = prompt_data.get("system_prompt", "").lower()
        persona_markers = ["você é", "product manager", "sênior", "senior"]
        matches = [m for m in persona_markers if m in text]
        assert matches, (
            "Prompt não define uma persona reconhecível. "
            f"Esperado pelo menos um destes marcadores: {persona_markers}"
        )

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        text = prompt_data.get("system_prompt", "")
        text_lower = text.lower()
        mentions_markdown = "markdown" in text_lower
        mentions_user_story_format = (
            "como" in text_lower and "eu quero" in text_lower and "para que" in text_lower
        )
        assert mentions_markdown or mentions_user_story_format, (
            "Prompt não menciona formato Markdown nem o template "
            "'Como ... Eu quero ... Para que ...'"
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        text = prompt_data.get("system_prompt", "")
        text_lower = text.lower()
        exemplo_count = text_lower.count("exemplo")
        bug_label = text_lower.count("bug:")
        resposta_label = text_lower.count("resposta:")
        has_examples = exemplo_count >= 2 or (bug_label >= 2 and resposta_label >= 2)
        assert has_examples, (
            "Prompt não contém ao menos 2 exemplos de entrada/saída. "
            f"Encontrado: 'exemplo'={exemplo_count}, 'bug:'={bug_label}, "
            f"'resposta:'={resposta_label}"
        )

    def test_prompt_no_todos(self, yaml_text):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        lowered = yaml_text.lower()
        assert "[todo]" not in lowered, "YAML contém marcador '[TODO]' não preenchido"
        assert "todo:" not in lowered, "YAML contém marcador 'TODO:' não preenchido"

    def test_minimum_techniques(self, prompt_data):
        """Verifica se ao menos 2 técnicas foram listadas em techniques_applied."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista"
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)} "
            f"({techniques})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
