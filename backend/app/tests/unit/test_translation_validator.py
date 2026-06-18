from unittest.mock import patch, MagicMock

from app.services.translation.translation_validator import (
    TranslationValidator,
    ValidationResult,
    ValidationStatus,
    validate_translation_provider,
)
from app.services.translation.translation_config import ProviderConfig


class TestValidationStatus:
    def test_status_values(self):
        assert ValidationStatus.OK == "ok"
        assert ValidationStatus.ERROR == "error"
        assert ValidationStatus.API_KEY_INVALID == "api_key_invalid"
        assert ValidationStatus.MODEL_INVALID == "model_invalid"
        assert ValidationStatus.MODEL_DEPRECATED == "model_deprecated"

    def test_status_count(self):
        assert len(ValidationStatus) == 5


class TestValidationResult:
    def test_is_ok_returns_true_for_ok(self):
        result = ValidationResult(
            status=ValidationStatus.OK,
            provider="test",
            api_key_valid=True,
            model_valid=True,
            model_used="m1",
            available_models=[],
            user_message="",
            details="",
        )
        assert result.is_ok is True

    def test_is_ok_returns_true_for_model_deprecated(self):
        result = ValidationResult(
            status=ValidationStatus.MODEL_DEPRECATED,
            provider="test",
            api_key_valid=True,
            model_valid=True,
            model_used="m1",
            available_models=["m2"],
            user_message="",
            details="",
        )
        assert result.is_ok is True

    def test_is_ok_returns_false_for_error(self):
        result = ValidationResult(
            status=ValidationStatus.ERROR,
            provider="test",
            api_key_valid=False,
            model_valid=False,
            model_used="",
            available_models=[],
            user_message="",
            details="",
        )
        assert result.is_ok is False

    def test_is_ok_returns_false_for_api_key_invalid(self):
        result = ValidationResult(
            status=ValidationStatus.API_KEY_INVALID,
            provider="test",
            api_key_valid=False,
            model_valid=False,
            model_used="m1",
            available_models=[],
            user_message="",
            details="",
        )
        assert result.is_ok is False

    def test_is_ok_returns_false_for_model_invalid(self):
        result = ValidationResult(
            status=ValidationStatus.MODEL_INVALID,
            provider="test",
            api_key_valid=True,
            model_valid=False,
            model_used="m1",
            available_models=["m2"],
            user_message="",
            details="",
        )
        assert result.is_ok is False


class TestValidateProviderFunctional:
    def test_unknown_provider_returns_error(self):
        result = TranslationValidator.validate_provider("nonexistent")
        assert result.status == ValidationStatus.ERROR
        assert result.api_key_valid is False
        assert result.model_valid is False
        assert "nonexistent" in result.user_message

    @patch.object(
        TranslationValidator, "_validate_api_key", return_value=(False, "No API key")
    )
    @patch.object(
        TranslationValidator, "_validate_model", return_value=(True, "gpt-4o", "")
    )
    def test_no_api_key_returns_api_key_invalid(self, mock_model, mock_key):
        result = TranslationValidator.validate_provider("openai", api_key=None)
        assert result.status == ValidationStatus.API_KEY_INVALID
        assert result.api_key_valid is False

    @patch.object(TranslationValidator, "_validate_api_key", return_value=(True, ""))
    @patch.object(
        TranslationValidator, "_validate_model", return_value=(True, "gpt-4o", "")
    )
    def test_valid_openai_with_explicit_model(self, mock_model, mock_key):
        result = TranslationValidator.validate_provider(
            "openai", api_key="sk-xxx", model="gpt-4o"
        )
        assert result.status == ValidationStatus.OK
        assert result.api_key_valid is True
        assert result.model_valid is True
        assert result.model_used == "gpt-4o"

    @patch.object(TranslationValidator, "_validate_api_key", return_value=(True, ""))
    @patch.object(
        TranslationValidator, "_validate_model", return_value=(True, "gpt-4o", "")
    )
    def test_valid_openai_with_default_model(self, mock_model, mock_key):
        result = TranslationValidator.validate_provider("openai", api_key="sk-xxx")
        assert result.status == ValidationStatus.OK
        assert result.model_used == "gpt-4o"

    @patch.object(TranslationValidator, "_validate_api_key", return_value=(True, ""))
    @patch.object(
        TranslationValidator,
        "_validate_model",
        return_value=(True, "claude-3-5-sonnet-20241022", ""),
    )
    def test_valid_claude_provider(self, mock_model, mock_key):
        result = TranslationValidator.validate_provider("claude", api_key="sk-ant-xxx")
        assert result.status == ValidationStatus.OK
        assert result.model_used == "claude-3-5-sonnet-20241022"

    @patch.object(
        TranslationValidator,
        "_validate_api_key",
        return_value=(False, "401 Unauthorized"),
    )
    def test_api_key_401_status(self, mock_key):
        result = TranslationValidator.validate_provider("openai", api_key="sk-bad")
        assert result.status == ValidationStatus.API_KEY_INVALID
        assert result.details == "API klju\u010d za openai nije validan"
        assert "401" in result.user_message

    @patch.object(
        TranslationValidator, "_validate_api_key", return_value=(False, "403 Forbidden")
    )
    def test_api_key_403_status(self, mock_key):
        result = TranslationValidator.validate_provider("openai", api_key="sk-bad")
        assert result.status == ValidationStatus.API_KEY_INVALID

    @patch.object(
        TranslationValidator,
        "_validate_api_key",
        return_value=(False, "429 Rate limited"),
    )
    def test_api_key_429_status(self, mock_key):
        result = TranslationValidator.validate_provider("openai", api_key="sk-bad")
        assert result.status == ValidationStatus.API_KEY_INVALID

    @patch.object(
        TranslationValidator,
        "_validate_api_key",
        return_value=(False, "500 Server Error"),
    )
    def test_api_key_other_status(self, mock_key):
        result = TranslationValidator.validate_provider("openai", api_key="sk-bad")
        assert result.status == ValidationStatus.API_KEY_INVALID


DEFAULT_CONFIGS = {
    "openai": ProviderConfig(
        name="OpenAI",
        default_model="gpt-4o",
        fallback_models=["gpt-4o-mini"],
        test_endpoint="/v1/models",
        auth_header="Bearer",
    ),
    "claude": ProviderConfig(
        name="Claude",
        default_model="claude-3-5-sonnet-20241022",
        fallback_models=["claude-3-haiku-20240307"],
        test_endpoint="/v1/messages",
        auth_header="Bearer",
    ),
    "deepseek": ProviderConfig(
        name="DeepSeek",
        default_model="deepseek-chat",
        fallback_models=["deepseek-coder"],
        test_endpoint="/v1/chat/completions",
        auth_header="Bearer",
    ),
    "groq": ProviderConfig(
        name="Groq",
        default_model="llama-3.1-8b-instant",
        fallback_models=["llama-3.3-70b-versatile"],
        test_endpoint="/v1/chat/completions",
        auth_header="Bearer",
    ),
    "mistral": ProviderConfig(
        name="Mistral",
        default_model="mistral-small-latest",
        fallback_models=["mistral-medium-latest"],
        test_endpoint="/v1/chat/completions",
        auth_header="Bearer",
    ),
}


class TestValidateApiKey:
    def test_no_api_key_returns_false(self):
        valid, msg = TranslationValidator._validate_api_key(
            "openai", None, DEFAULT_CONFIGS["openai"]
        )
        assert valid is False
        assert "API klju\u010d nije pode\u0161en" in msg

    def test_rest_providers_skip_validation(self):
        rest_providers = ["deepl", "google", "simplytranslate", "ollama"]
        for prov in rest_providers:
            valid, msg = TranslationValidator._validate_api_key(
                prov, "some-key", DEFAULT_CONFIGS.get(prov, DEFAULT_CONFIGS["openai"])
            )
            assert valid is True
            assert msg == ""

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_groq_valid_key(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "groq", "gsk-xxx", DEFAULT_CONFIGS["groq"]
        )
        assert valid is True
        assert msg == ""

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_mistral_valid_key(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "mistral", "mist-xxx", DEFAULT_CONFIGS["mistral"]
        )
        assert valid is True

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_deepseek_valid_key(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "deepseek", "sk-ds-xxx", DEFAULT_CONFIGS["deepseek"]
        )
        assert valid is True

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_timeout_returns_false(self, mock_post):
        from httpx import TimeoutException

        mock_post.side_effect = TimeoutException("timeout")
        valid, msg = TranslationValidator._validate_api_key(
            "groq", "gsk-xxx", DEFAULT_CONFIGS["groq"]
        )
        assert valid is False
        assert "Timeout" in msg

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_generic_exception_returns_true(self, mock_post):
        mock_post.side_effect = Exception("connection error")
        valid, msg = TranslationValidator._validate_api_key(
            "groq", "gsk-xxx", DEFAULT_CONFIGS["groq"]
        )
        assert valid is True
        assert msg == ""

    @patch("app.services.translation.translation_validator.httpx.get")
    def test_openai_valid_key(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "openai", "sk-xxx", DEFAULT_CONFIGS["openai"]
        )
        assert valid is True
        assert msg == ""

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_claude_valid_key(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "claude", "sk-ant-xxx", DEFAULT_CONFIGS["claude"]
        )
        assert valid is True
        assert msg == ""

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_http_401_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "groq", "gsk-bad", DEFAULT_CONFIGS["groq"]
        )
        assert valid is False
        assert "istekao" in msg

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_http_403_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "groq", "gsk-bad", DEFAULT_CONFIGS["groq"]
        )
        assert valid is False
        assert "Pristup odbijen" in msg

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_http_429_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "groq", "gsk-bad", DEFAULT_CONFIGS["groq"]
        )
        assert valid is False
        assert "Prekora\u010den limit" in msg

    @patch("app.services.translation.translation_validator.httpx.post")
    def test_http_other_status_code(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        valid, msg = TranslationValidator._validate_api_key(
            "groq", "gsk-bad", DEFAULT_CONFIGS["groq"]
        )
        assert valid is False
        assert "500" in msg


class TestValidateModel:
    def test_rest_providers_always_valid(self):
        rest = ["deepl", "google", "simplytranslate", "ollama"]
        for prov in rest:
            cfg = DEFAULT_CONFIGS.get(prov)
            valid, model, msg = TranslationValidator._validate_model(
                prov, "any-model", cfg
            )
            assert valid is True
            assert model == "any-model"

    def test_default_model_is_valid(self):
        valid, model, msg = TranslationValidator._validate_model(
            "openai", "gpt-4o", DEFAULT_CONFIGS["openai"]
        )
        assert valid is True
        assert model == "gpt-4o"

    def test_fallback_model_is_valid(self):
        valid, model, msg = TranslationValidator._validate_model(
            "openai", "gpt-4o-mini", DEFAULT_CONFIGS["openai"]
        )
        assert valid is True
        assert model == "gpt-4o-mini"

    def test_groq_fallback_model_is_valid(self):
        valid, model, msg = TranslationValidator._validate_model(
            "groq", "llama-3.3-70b-versatile", DEFAULT_CONFIGS["groq"]
        )
        assert valid is True
        assert model == "llama-3.3-70b-versatile"

    def test_unknown_model_falls_back_to_default(self):
        valid, model, msg = TranslationValidator._validate_model(
            "openai", "nonexistent-model", DEFAULT_CONFIGS["openai"]
        )
        assert valid is False
        assert model == "gpt-4o"


class TestValidateProviderBranching:
    @patch.object(TranslationValidator, "_validate_api_key", return_value=(True, ""))
    @patch.object(
        TranslationValidator,
        "_validate_model",
        return_value=(False, "gpt-4o", "Model 'x' nije dostupan"),
    )
    def test_model_invalid_with_mocking(self, mock_model, mock_key):
        result = TranslationValidator.validate_provider(
            "openai", api_key="sk-xxx", model="nonexistent"
        )
        assert result.status == ValidationStatus.MODEL_INVALID
        assert result.model_valid is False
        assert result.model_used == "gpt-4o"

    @patch.object(TranslationValidator, "_validate_api_key", return_value=(True, ""))
    @patch.object(
        TranslationValidator,
        "_validate_model",
        return_value=(False, "gpt-4o", "Model 'gpt-4o' deprecated"),
    )
    def test_model_deprecated_with_mocking(self, mock_model, mock_key):
        result = TranslationValidator.validate_provider(
            "openai", api_key="sk-xxx", model="gpt-4o"
        )
        assert result.status == ValidationStatus.MODEL_DEPRECATED
        assert result.model_valid is True
        assert result.model_used == "gpt-4o"


class TestValidateTranslationProviderWrapper:
    @patch.object(TranslationValidator, "validate_provider")
    def test_wrapper_calls_validator(self, mock_validate):
        mock_validate.return_value = ValidationResult(
            status=ValidationStatus.OK,
            provider="openai",
            api_key_valid=True,
            model_valid=True,
            model_used="gpt-4o",
            available_models=[],
            user_message="OK",
            details="",
        )
        result = validate_translation_provider(
            "openai", api_key="sk-xxx", model="gpt-4o"
        )
        mock_validate.assert_called_once_with("openai", "sk-xxx", "gpt-4o")
        assert result.status == ValidationStatus.OK
