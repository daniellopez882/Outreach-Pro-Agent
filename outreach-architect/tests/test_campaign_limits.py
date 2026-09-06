"""
One request cannot ask for unbounded work.

``POST /campaigns`` accepted any number of ``lead_ids``; each lead costs several
model calls, so an authenticated caller could run up the provider bill with a
single request. The list is now bounded and validation answers 422 before any
model is called.
"""

from __future__ import annotations

from main import MAX_LEADS_PER_REQUEST


def _body(ids):
    return {"lead_ids": ids, "company_context": "ctx", "value_proposition": "vp"}


class TestCampaignBatchBound:
    def test_too_many_leads_is_a_422(self, client, auth_headers):
        r = client.post(
            "/campaigns",
            json=_body(list(range(1, MAX_LEADS_PER_REQUEST + 2))),
            headers=auth_headers,
        )
        assert r.status_code == 422
        assert "lead_ids" in r.text

    def test_an_empty_list_is_a_422(self, client, auth_headers):
        r = client.post("/campaigns", json=_body([]), headers=auth_headers)
        assert r.status_code == 422

    def test_the_bound_is_advertised_in_the_schema(self, client):
        schema = client.get("/openapi.json").json()
        prop = schema["components"]["schemas"]["CampaignRequest"]["properties"]["lead_ids"]
        assert prop["maxItems"] == MAX_LEADS_PER_REQUEST
        assert prop["minItems"] == 1
