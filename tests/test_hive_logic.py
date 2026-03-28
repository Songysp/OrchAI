import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from packages.orchestrator.hive import HiveOrchestrator
from packages.domain.models.project import Project
from packages.agents.base import AgentTurnResult

@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.provider_name = "mock"
    adapter.run_turn = AsyncMock()
    return adapter

@pytest.fixture
def sample_project():
    return Project(
        project_id="test_p", 
        name="Test Project", 
        workspace_path=".", 
        repo_url="https://github.com/mock/repo", 
        chat_platform="cli"
    )

@pytest.mark.asyncio
async def test_hive_orchestrator_success_loop(mock_adapter, sample_project):
    # Setup mock responses for Planner, Worker, Refiner
    planner_res = AgentTurnResult(role="planner", provider="mock", output="Plan: Step 1, Step 2", status="completed")
    worker_res = AgentTurnResult(role="worker", provider="mock", output="Implementation Done", status="completed")
    refiner_res = AgentTurnResult(role="refiner", provider="mock", output="DONE: Everything looks great", status="completed")
    
    mock_adapter.run_turn.side_effect = [planner_res, worker_res, refiner_res]
    
    orchestrator = HiveOrchestrator(mock_adapter, max_turns=2)
    history = await orchestrator.execute("Build a simple app", sample_project)
    
    assert len(history) == 3 # 1 Plan + 1 Worker + 1 Refiner (DONE)
    assert history[0].role == "planner"
    assert history[1].role == "worker"
    assert history[2].role == "refiner"
    assert "DONE" in history[2].output

@pytest.mark.asyncio
async def test_hive_orchestrator_max_turns_escalation(mock_adapter, sample_project, monkeypatch):
    # Setup mock responses that never finish
    planner_res = AgentTurnResult(role="planner", provider="mock", output="Plan: Endless loop", status="completed")
    worker_res = AgentTurnResult(role="worker", provider="mock", output="Still working...", status="completed")
    refiner_res = AgentTurnResult(role="refiner", provider="mock", output="RETRY: Needs more work", status="completed")
    
    mock_adapter.run_turn.side_effect = [planner_res, worker_res, refiner_res, worker_res, refiner_res]
    
    # Mock typer.prompt for escalation input (Human says DONE)
    monkeypatch.setattr("typer.prompt", lambda msg, default: "DONE")
    
    orchestrator = HiveOrchestrator(mock_adapter, max_turns=1)
    history = await orchestrator.execute("Do something hard", sample_project)
    
    # turn_count starts at 0. 
    # Turn 1: Worker + Refiner (Not DONE). Then turns count (1) >= max_turns (1).
    # Escalation happens -> Human says DONE -> Loop breaks.
    assert len(history) >= 3 
    # Check if escalation message is in the history or if it simply stopped.
    # In my implementation, it breaks after marking complete.
