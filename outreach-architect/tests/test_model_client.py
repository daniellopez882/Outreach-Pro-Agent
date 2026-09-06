"""
The model client is built on first use, not at import, and canned output says so.

Reproduced defect: ``KimiAgent.__init__`` called ``OpenAI(api_key=None)`` when
no key was configured, which raises ``OpenAIError``. The agent is instantiated
at module import, so importing ``orchestrator`` -- and with it the code behind
``POST /campaigns`` and ``POST /campaigns/{id}/send`` -- failed on any machine
without a DEEPSEEK or KIMI key. The README's "falls back to canned responses
when no provider key is set, and says so in its output" was doubly untrue: the
import died first, and the canned output carried no marker.
"""

from __future__ import annotations

import pytest

from config import settings


@pytest.fixture
def no_keys(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", None)
    monkeypatch.setattr(settings, "kimi_api_key", None)


class TestClientConstruction:
    def test_the_agent_can_be_built_without_any_key(self, no_keys):
        from kimi_agent import KimiAgent

        agent = KimiAgent()  # used to raise openai.OpenAIError
        assert agent.engine == "kimi"
        assert agent.model == settings.kimi_model

    def test_the_client_is_only_built_when_asked_for_and_needs_a_key(self, no_keys):
        from kimi_agent import KimiAgent

        agent = KimiAgent()
        with pytest.raises(RuntimeError, match="KIMI_API_KEY"):
            agent.client  # noqa: B018

    def test_a_configured_key_builds_the_client_lazily(self, monkeypatch):
        monkeypatch.setattr(settings, "deepseek_api_key", "sk-looks-real")
        from kimi_agent import KimiAgent

        agent = KimiAgent()
        assert agent.engine == "deepseek"
        assert agent._client is None
        assert agent.client.api_key == "sk-looks-real"
        assert agent._client is not None


class TestCannedResponses:
    def test_no_key_means_canned_responses_not_a_crash(self, no_keys):
        from kimi_agent import KimiAgent

        result = KimiAgent()._call_kimi([{"role": "user", "content": "Analyze this lead"}])
        assert result["content"]
        assert result["mock"] is True

    async def test_a_canned_analysis_is_labelled(self, no_keys):
        from kimi_agent import KimiAgent

        analysis = await KimiAgent().analyze_lead_profile({"name": "Ada", "company": "Engines"})
        assert analysis["generated_by"] == "canned"

    async def test_a_canned_draft_is_labelled(self, no_keys):
        from kimi_agent import KimiAgent

        email = await KimiAgent().generate_personalized_email(
            lead_data={"name": "Ada", "company": "Engines", "job_title": "Engineer"},
            analysis={"pain_points": [], "interests": [], "trigger_events": []},
            company_context="ctx",
            value_proposition="vp",
        )
        assert email["generated_by"] == "canned"
