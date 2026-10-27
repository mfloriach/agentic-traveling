from pathlib import Path
from pydantic import BaseModel, Field
import yaml


class AgentConfig(BaseModel):
    name: str
    model: str
    temperature: float = Field(ge=0, le=2)
    max_output_tokens: int = Field(gt=0)
    max_concurrency: int = Field(gt=0)
    system_prompt: str


def load_agent_configs() -> dict[str, AgentConfig]:
    path = Path("config/agents.yaml")
    raw = yaml.safe_load(path.read_text())
    return {
        name: AgentConfig.model_validate(config)
        for name, config in raw["agents"].items()
    }