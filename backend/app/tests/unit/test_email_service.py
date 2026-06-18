# -*- coding: utf-8 -*-
"""
Testovi za EmailService
"""

from unittest.mock import patch, MagicMock
from app.services.email_service import EmailService


class TestEmailServiceInit:
    """Testovi za inicijalizaciju EmailService."""

    def test_init_with_settings(self):
        """Test inicijalizacije sa podesenim settings."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "user@example.com"
            mock_settings.SMTP_PASSWORD = "password123"
            mock_settings.SMTP_TLS = True
            mock_settings.EMAIL_FROM = "noreply@example.com"

            service = EmailService()

            assert service.host == "smtp.example.com"
            assert service.port == 587
            assert service.user == "user@example.com"
            assert service.password == "password123"
            assert service.tls is True
            assert service.from_addr == "noreply@example.com"


class TestEmailServiceIsConfigured:
    """Testovi za is_configured metodu."""

    def test_is_configured_when_all_present(self):
        """Test is_configured kada su svi parametri prisutni."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"

            service = EmailService()
            assert service.is_configured() is True

    def test_is_configured_missing_host(self):
        """Test is_configured kada nedostaje host."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"

            service = EmailService()
            assert service.is_configured() is False

    def test_is_configured_missing_user(self):
        """Test is_configured kada nedostaje user."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = ""
            mock_settings.SMTP_PASSWORD = "password"

            service = EmailService()
            assert service.is_configured() is False

    def test_is_configured_missing_password(self):
        """Test is_configured kada nedostaje password."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = ""

            service = EmailService()
            assert service.is_configured() is False


class TestEmailServiceSend:
    """Testovi za send metode."""

    def test_send_not_configured(self):
        """Test slanja kada email nije konfigurisan."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""
            mock_settings.SMTP_USER = ""
            mock_settings.SMTP_PASSWORD = ""
            mock_settings.EMAIL_FROM = "noreply@example.com"

            service = EmailService()
            result = service._send("test@example.com", "Test Subject", "<p>Test</p>")

            assert result is False

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_success(self, mock_smtp):
        """Test uspesnog slanja emaila."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "user@example.com"
            mock_settings.SMTP_PASSWORD = "password123"
            mock_settings.SMTP_TLS = True
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            service = EmailService()
            result = service._send("to@example.com", "Test Subject", "<p>Test</p>")

            assert result is True
            mock_server.sendmail.assert_called_once()

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_with_text_fallback(self, mock_smtp):
        """Test slanja emaila sa text fallbackom."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "user@example.com"
            mock_settings.SMTP_PASSWORD = "password123"
            mock_settings.SMTP_TLS = True
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            service = EmailService()
            result = service._send(
                "to@example.com", "Test Subject", "<p>Test</p>", "Test text"
            )

            assert result is True

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_exception(self, mock_smtp):
        """Test slanja kada dodje do exceptiona."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "user@example.com"
            mock_settings.SMTP_PASSWORD = "password123"
            mock_settings.SMTP_TLS = True
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_smtp.side_effect = Exception("Connection failed")

            service = EmailService()
            result = service._send("to@example.com", "Test Subject", "<p>Test</p>")

            assert result is False


class TestSendWelcome:
    """Testovi za send_welcome metodu."""

    @patch("app.services.email_service.EmailService._send")
    def test_send_welcome_with_name(self, mock_send):
        """Test send_welcome sa imenom."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_welcome("user@example.com", "Petar Peric")

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert "user@example.com" in call_args[0]
            assert "Dobrodosli" in call_args[1]

    @patch("app.services.email_service.EmailService._send")
    def test_send_welcome_without_name(self, mock_send):
        """Test send_welcome bez imena."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_welcome("petar@example.com", "")

            assert result is True


class TestSendDailyReminder:
    """Testovi za send_daily_reminder metodu."""

    @patch("app.services.email_service.EmailService._send")
    def test_send_daily_reminder_with_quizzes(self, mock_send):
        """Test daily reminder sa kvizovima."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_daily_reminder(
                "user@example.com", "Petar", ["Kviz 1", "Kviz 2"], 5
            )

            assert result is True
            mock_send.assert_called_once()

    @patch("app.services.email_service.EmailService._send")
    def test_send_daily_reminder_no_quizzes(self, mock_send):
        """Test daily reminder bez kvizova."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_daily_reminder("user@example.com", "Petar", [], 0)

            assert result is True


class TestSendWeeklySummary:
    """Testovi za send_weekly_summary metodu."""

    @patch("app.services.email_service.EmailService._send")
    def test_send_weekly_summary_achieved(self, mock_send):
        """Test weekly summary kada je cilj postignut."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_weekly_summary(
                "user@example.com",
                "Petar",
                week_completed=7,
                week_goal=7,
                avg_score=85,
                streak=5,
                best_quiz="Kviz iz Istorije",
            )

            assert result is True

    @patch("app.services.email_service.EmailService._send")
    def test_send_weekly_summary_not_achieved(self, mock_send):
        """Test weekly summary kada cilj nije postignut."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_weekly_summary(
                "user@example.com",
                "Petar",
                week_completed=3,
                week_goal=7,
                avg_score=65,
                streak=2,
            )

            assert result is True


class TestSendPasswordReset:
    """Testovi za send_password_reset metodu."""

    @patch("app.services.email_service.EmailService._send")
    def test_send_password_reset(self, mock_send):
        """Test password reset email."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_password_reset(
                "user@example.com", "Petar", "https://example.com/reset/abc123"
            )

            assert result is True


class TestSendDocumentProcessed:
    """Testovi za send_document_processed metodu."""

    @patch("app.services.email_service.EmailService._send")
    def test_send_document_processed(self, mock_send):
        """Test dokument obrađen email."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_document_processed(
                "user@example.com", "Petar", "Moj Dokument", 50, 25
            )

            assert result is True


class TestSendQuizCompleted:
    """Testovi za send_quiz_completed metodu."""

    @patch("app.services.email_service.EmailService._send")
    def test_send_quiz_completed_passed(self, mock_send):
        """Test kviz zavrsen - prosao."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_quiz_completed(
                "user@example.com",
                "Petar",
                "Kviz iz Matematike",
                score=8,
                total=10,
                passed=True,
            )

            assert result is True

    @patch("app.services.email_service.EmailService._send")
    def test_send_quiz_completed_failed(self, mock_send):
        """Test kviz zavrsen - nisi prosao."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_quiz_completed(
                "user@example.com",
                "Petar",
                "Kviz iz Matematike",
                score=4,
                total=10,
                passed=False,
            )

            assert result is True


class TestSendChunksReady:
    """Testovi za send_chunks_ready metodu."""

    @patch("app.services.email_service.EmailService._send")
    def test_send_chunks_ready_success(self, mock_send):
        """Test uspešno slanje email-a kada su chunk-ovi kreirani."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_chunks_ready(
                to="user@example.com",
                full_name="Petar",
                document_title="VMware vSphere Priručnik",
                total_chunks=45,
                total_pages=12,
            )

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "user@example.com"
            assert "VMware vSphere Priručnik" in call_args[0][1]
            assert "45" in call_args[0][2]
            assert "12" in call_args[0][2]

    @patch("app.services.email_service.EmailService._send")
    def test_send_chunks_ready_empty_name(self, mock_send):
        """Test sa praznim imenom koristi email username."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_chunks_ready(
                to="user@example.com",
                full_name="",
                document_title="Test Dokument",
                total_chunks=10,
                total_pages=5,
            )

            assert result is True


class TestSendTranslationReady:
    """Testovi za send_translation_ready metodu."""

    @patch("app.services.email_service.EmailService._send")
    def test_send_translation_ready_success(self, mock_send):
        """Test uspešno slanje email-a kada je prevod završen."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_translation_ready(
                to="user@example.com",
                full_name="Petar",
                document_title="VMware vSphere Priručnik",
                source_language="en",
                target_language="sr",
                total_chunks=45,
            )

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "user@example.com"
            assert "Prevod dokumenta završen" in call_args[0][1]

    @patch("app.services.email_service.EmailService._send")
    def test_send_translation_ready_language_mapping(self, mock_send):
        """Test mapiranje jezičkih kodova u imena."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_translation_ready(
                to="user@example.com",
                full_name="Petar",
                document_title="Test",
                source_language="de",
                target_language="fr",
                total_chunks=20,
            )

            assert result is True
            call_args = mock_send.call_args
            html_content = call_args[0][2]
            assert "German" in html_content
            assert "French" in html_content

    @patch("app.services.email_service.EmailService._send")
    def test_send_translation_ready_empty_name(self, mock_send):
        """Test sa praznim imenom koristi email username."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.EMAIL_FROM = "noreply@example.com"

            mock_send.return_value = True

            service = EmailService()
            result = service.send_translation_ready(
                to="user@example.com",
                full_name="",
                document_title="Test Dokument",
                source_language="en",
                target_language="sr",
                total_chunks=10,
            )

            assert result is True
