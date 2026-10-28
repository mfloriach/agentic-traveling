"""Tests for dag/travel-planner/services/travel_planner.py.

Covers:
- agent configuration loading and how agents get built from it
- full plan_trip flow with mocked agents, asserting context wiring, prompts and logs
"""

import asyncio
import importlib
import logging
import pathlib
import sys
from types import SimpleNamespace

import pytest

# the package directory is named "travel-planner" (hyphen), so import via importlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "src" / "dag"))
tp = importlib.import_module("travel-planner.services.travel_planner")


# ---------------------------------------------------------------- fake agents


USAGE = SimpleNamespace(requests=1, input_tokens=11, output_tokens=22, total_tokens=33)

FAKE_OUTPUTS = {
    "destination_agent": SimpleNamespace(destination="Paris"),
    "flight_agent": SimpleNamespace(from_city="Berlin", arrivla_time="18:30"),
    "hotel_agent": SimpleNamespace(
        name="Hotel du Collectionneur",
        location="9th arrondissement",
        stars=5,
        price_per_night_usd=400,
    ),
    "activity_agent": SimpleNamespace(
        personalized_for="John",
        top_activities=["Louvre", "Seine cruise"],
    ),
}


class FakeAgent:
    """Stands in for pydantic_ai.Agent: records build kwargs and run() calls."""

    built: list["FakeAgent"] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        # convenience accessors matching the config fields
        self.model = kwargs["model"]
        self.temperature = kwargs["model_settings"]["temperature"]
        self.max_output_tokens = kwargs["model_settings"]["max_tokens"]
        self.system_prompt = kwargs["system_prompt"]
        FakeAgent.built.append(self)

    async def run(self, prompt, deps=None):
        self.calls.append((prompt, deps))
        return SimpleNamespace(output=FAKE_OUTPUTS[self.kwargs["name"]], usage=lambda: USAGE)


@pytest.fixture
def planner(monkeypatch):
    monkeypatch.setattr(tp, "Agent", FakeAgent)
    FakeAgent.built.clear()
    return tp.TravelPlanner(tp.TravelDeps(user_name="John", origin_city="Berlin"))


# ------------------------------------------------------------------- configs


def test_load_agent_configs():
    configs = tp.load_agent_configs()
    assert set(configs) == {"destination", "flight", "hotel", "activities"}
    for name, cfg in configs.items():
        assert cfg.name
        assert ":" in cfg.model  # provider-qualified model string
        assert 0 <= cfg.temperature <= 2
        assert cfg.max_output_tokens > 0
        assert cfg.system_prompt.strip()


def test_agents_built_from_config(planner):
    by_name = {a.kwargs["name"]: a for a in FakeAgent.built}
    assert set(by_name) == {"destination_agent", "flight_agent", "hotel_agent", "activity_agent"}

    assert by_name["destination_agent"].model == "openai:gpt-4o"
    assert by_name["destination_agent"].temperature == 0.3
    assert by_name["destination_agent"].max_output_tokens == 500

    for name in ("flight_agent", "hotel_agent", "activity_agent"):
        agent = by_name[name]
        assert agent.model == "anthropic:claude-haiku-4-5"
        assert agent.max_output_tokens == 1000
        assert agent.system_prompt

    assert by_name["hotel_agent"].temperature == 0.5
    assert by_name["activity_agent"].temperature == 0.2


# ----------------------------------------------------------------- plan_trip


def test_plan_trip_success(planner, caplog):
    with caplog.at_level(logging.INFO):
        asyncio.run(planner.plan_trip("I love towers"))

    # context wiring: each step feeds the next
    assert planner.ctx.destination == "Paris"
    assert planner.ctx.from_city == "Berlin"
    assert planner.ctx.arrival_time == "18:30"
    assert planner.ctx.hotel_name == "Hotel du Collectionneur"
    assert planner.ctx.hotel_location == "9th arrondissement"

    # prompts chain earlier results; deps always passed
    (dest_prompt, dest_deps) = planner.destination_agent.calls[0]
    (flight_prompt, flight_deps) = planner.flight_agent.calls[0]
    (hotel_prompt, _) = planner.hotel_agent.calls[0]
    (act_prompt, _) = planner.activity_agent.calls[0]

    assert "I love towers" in dest_prompt
    assert dest_deps is planner.deps
    assert "from Berlin to Paris" in flight_prompt
    assert flight_deps is planner.deps
    assert "arriving at 18:30" in hotel_prompt
    assert "close to 9th arrondissement" in act_prompt

    # agent decorator logs: started / completed per agent, in order
    def events(msg):
        return [r for r in caplog.records if r.getMessage() == msg]

    started = events("agent.started")
    completed = events("agent.completed")
    assert [r.__dict__["agent_name"] for r in started] == [
        "handle_destination",
        "handle_flight",
        "handle_hotel",
        "handle_activities",
    ]
    assert [r.__dict__["agent_name"] for r in completed] == [
        "handle_destination",
        "handle_flight",
        "handle_hotel",
        "handle_activities",
    ]

    for r in completed:
        assert r.__dict__["requests"] == 1
        assert r.__dict__["input_tokens"] == 11
        assert r.__dict__["output_tokens"] == 22
        assert r.__dict__["total_tokens"] == 33
        assert r.__dict__["duration_ms"] >= 0

    # trip level logs
    assert events("trip.started") and events("trip.completed")
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


def test_plan_trip_failure_logs(planner, caplog, monkeypatch):
    async def boom(prompt, deps=None):
        raise RuntimeError("activities exploded")

    monkeypatch.setattr(planner.activity_agent, "run", boom)

    with caplog.at_level(logging.INFO), pytest.raises(RuntimeError):
        asyncio.run(planner.plan_trip("I love towers"))

    messages = [r.getMessage() for r in caplog.records]
    assert "trip.failed" in messages
    failed = [r for r in caplog.records if r.getMessage() == "agent.failed"]
    assert [r.__dict__["agent_name"] for r in failed] == ["handle_activities"]
    # hotel still ran fine before the failure
    assert planner.ctx.hotel_name == "Hotel du Collectionneur"
