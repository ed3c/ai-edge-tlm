from edge_tlm.webview_policy import WebViewPolicy


def test_webview_policy_denies_unlisted_origin_and_weak_csp():
    policy = WebViewPolicy(frozenset({"app://local", "https://skills.example.test"}))
    assert policy.admit_url("https://skills.example.test/app")
    assert not policy.admit_url("http://skills.example.test/app")
    assert not policy.admit_url("https://evil.example/app")
    assert policy.validate_csp("default-src 'none'; object-src 'none'; script-src 'self'")
    assert not policy.validate_csp("default-src *")
