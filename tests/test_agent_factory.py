from pathlib import Path

from packages.agents import AgentFactory, ClaudeAdapter, CodexAdapter, GeminiAdapter
from packages.domain.models import AgentMapping, Project


def test_agent_factory_returns_provider_adapter_and_selection() -> None:
    project = Project(
        project_id="project-agents",
        repo_url="https://github.com/example/project-agents",
        workspace_path="workspaces/project-agents",
        chat_platform="slack",
        agent_mapping={
            "representative": AgentMapping(
                role="representative",
                provider="claude",
                model="claude-sonnet",
                parameters={"temperature": 0.2},
            ),
            "planner": AgentMapping(
                role="planner",
                provider="gemini",
                model="gemini-pro",
                parameters={"temperature": 0.1},
            ),
            "builder": AgentMapping(
                role="builder",
                provider="codex",
                model="codex-latest",
                parameters={"temperature": 0.0},
            ),
        },
    )

    factory = AgentFactory(
        {
            "claude": ClaudeAdapter(),
            "gemini": GeminiAdapter(),
            "codex": CodexAdapter(),
        }
    )

    adapter, selection = factory.get_agent("builder", project)

    assert isinstance(adapter, CodexAdapter)
    assert selection.role == "builder"
    assert selection.provider == "codex"
    assert selection.model == "codex-latest"
    assert selection.parameters["temperature"] == 0.0
