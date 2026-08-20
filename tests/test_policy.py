from edge_tlm.policy import PolicyDecision, ProviderCandidate, Requirements, select_provider


def test_sensitive_offline_request_rejects_cloud():
    result = select_provider(
        Requirements(True, "sensitive", False),
        [ProviderCandidate("cloud", True, False, frozenset({"text"}), "stable", 0)],
    )
    assert result.decision is PolicyDecision.NO_PROVIDER
    assert result.provider is None


def test_preferred_admitted_provider_wins():
    result = select_provider(
        Requirements(True, "local-only", False, preferred_provider="embedded"),
        [
            ProviderCandidate("system", True, True, frozenset({"text"}), "system-managed", 0),
            ProviderCandidate("embedded", True, True, frozenset({"text"}), "stable", 10),
        ],
    )
    assert result.provider and result.provider.provider_id == "embedded"
