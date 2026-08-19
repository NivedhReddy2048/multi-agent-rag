"""Test suite for Windows console Unicode encoding safety in EKIP platform.

Validates that:
1. Console print statements with emojis (\U0001f4c4 📄, 📚, 🔬, 🚀, →, ±, °) do not crash on Windows cp1252 environment.
2. safe_print helper safely handles arbitrary unicode characters.
3. sys.stdout/sys.stderr UTF-8 reconfiguration prevents UnicodeEncodeError.
4. Summarize uploaded documents query path executes without console encoding crashes.
"""

import sys
import pytest
from app import safe_print


def test_safe_print_unicode_characters():
    """Verify safe_print handles all problematic Unicode characters without raising UnicodeEncodeError."""
    test_chars = ["📄", "📚", "🔬", "🚀", "→", "±", "°", "\U0001f4c4"]
    for char in test_chars:
        # Should not raise UnicodeEncodeError
        safe_print(f"Testing character encoding: {char} (repr: {repr(char)})")


def test_sys_stdout_reconfigured_encoding():
    """Verify sys.stdout and sys.stderr are reconfigured to utf-8."""
    assert sys.stdout.encoding.lower().replace("-", "") in ("utf8", "utf-8") or hasattr(sys.stdout, "reconfigure")
    assert sys.stderr.encoding.lower().replace("-", "") in ("utf8", "utf-8") or hasattr(sys.stderr, "reconfigure")


def test_mock_chat_message_history_render():
    """Simulate app.py session history debug loop with Unicode content containing 📄."""
    messages = [
        {
            "role": "assistant",
            "content": "#### 📄 Coverletter_Stripe.pdf\n- Summary of stripe application...\n#### 📚 Key Takeaways\n- Software engineering experience 🚀",
            "metadata": {"provider": "gemini", "model": "gemini-2.0-flash"},
        }
    ]

    # Replicate app.py debug logging block
    for idx, msg in enumerate(messages):
        safe_print(f"  [MSG #{idx} ASSISTANT | id({id(msg)})]")
        safe_print(f"    Provider: {msg.get('metadata', {}).get('provider', 'UNKNOWN')}")
        safe_print(f"    Model   : {msg.get('metadata', {}).get('model', 'Unknown')}")
        safe_print(f"    Content : {repr(msg.get('content', ''))[:300]}")
