# -*- coding: utf-8 -*-
"""
===============================================================================
GENERATION MODULE TESTS
===============================================================================

Testovi za generation.py module — timeout override i restore logika.

Pokretanje:
    pytest tests/unit/test_generation.py -v
===============================================================================
"""

import pytest
from unittest.mock import MagicMock


class TestGenerateWithPrompt:
    """Testovi za generate_with_prompt() timeout override."""

    def _generate(self, client, prompt="test prompt", num=5):
        from app.services.quiz.generation import generate_with_prompt

        return generate_with_prompt(client, prompt, num)

    def test_timeout_overridden_before_call(self):
        """Client.timeout mora biti postavljen na PER_PROVIDER_TIMEOUT pre generate()."""
        from app.services.quiz.generation import PER_PROVIDER_TIMEOUT

        client = MagicMock()
        client.timeout = 120
        client.generate.return_value = (True, "[]", "")

        self._generate(client)

        assert client.timeout == PER_PROVIDER_TIMEOUT, (
            f"Timeout treba da bude {PER_PROVIDER_TIMEOUT}, a ne {client.timeout}"
        )

    def test_timeout_restored_after_call(self):
        """Originalni timeout mora biti restore-ovan posle generate()."""
        client = MagicMock()
        client.timeout = 120
        client.generate.return_value = (True, "[]", "")

        self._generate(client)

        assert client.timeout == 120, (
            f"Timeout treba da bude restore-ovan na 120, a ne {client.timeout}"
        )

    def test_timeout_restored_on_error(self):
        """Timeout mora biti restore-ovan čak i kad generate() baci exception."""
        client = MagicMock()
        client.timeout = 120
        client.generate.side_effect = RuntimeError("API failed")

        with pytest.raises(RuntimeError):
            self._generate(client)

        assert client.timeout == 120, (
            f"Timeout treba da bude restore-ovan na 120 i posle exception-a, "
            f"a ne {client.timeout}"
        )

    def test_generate_called_with_correct_args(self):
        """generate() mora biti pozvan sa prompt i num_questions argumentima."""
        client = MagicMock()
        client.timeout = 120
        client.generate.return_value = (True, '[{"q": "test"}]', "")

        self._generate(client, prompt="special prompt", num=10)

        client.generate.assert_called_once_with("special prompt", 10)

    def test_client_without_timeout_attribute(self):
        """Client bez timeout atributa ne sme da pukne."""
        client = MagicMock(spec=[])  # empty spec = no attributes
        client.generate.return_value = (True, "[]", "")

        result = self._generate(client)

        assert result == (True, "[]", "")

    def test_return_value_preserved(self):
        """Povratna vrednost generate() mora biti netaknuta."""
        client = MagicMock()
        client.timeout = 120
        expected = (True, '[{"q": "What?"}]', "")
        client.generate.return_value = expected

        result = self._generate(client)

        assert result == expected
