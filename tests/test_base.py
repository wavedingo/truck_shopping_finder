from __future__ import annotations

from scrapers.base import rotate_user_agent, detect_block


def test_rotate_user_agent_returns_nonempty_string():
    ua = rotate_user_agent()
    assert isinstance(ua, str) and len(ua) > 20


def test_rotate_user_agent_is_not_always_the_same():
    uas = {rotate_user_agent() for _ in range(30)}
    assert len(uas) > 1


def test_detect_block_on_cloudflare_title():
    assert detect_block("Just a moment...", "<body>some content here</body>") is True


def test_detect_block_on_normal_page():
    content = "<div class='vehicle-card'>listing content</div>" * 10
    assert detect_block("Used Toyota Tacoma for Sale", content) is False


def test_detect_block_on_empty_body():
    assert detect_block("Cars for Sale", "") is True


def test_detect_block_on_access_denied():
    assert detect_block("403 Forbidden", "<body>Access Denied</body>") is True
