# -*- coding: utf-8 -*-
"""
================================================================================
EMAIL SERVICE
================================================================================
Slanje email notifikacija korisnicima:
- Dnevni podsetnik (studyplan reminder)
- Dobrodošlica pri registraciji
- Nedeljni sažetak napretka

Verzija: 1.0.0
================================================================================
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Servis za slanje emailova putem SMTP."""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.tls = settings.SMTP_TLS
        self.from_addr = settings.EMAIL_FROM

    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password)

    def _send(self, to: str, subject: str, html: str, text: str = "") -> bool:
        if not self.is_configured():
            logger.warning("Email nije konfigurisan — preskačem slanje.")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = to
            if text:
                msg.attach(MIMEText(text, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))

            with smtplib.SMTP(self.host, self.port) as server:
                if self.tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_addr, to, msg.as_string())

            logger.info(f"Email poslat: {to} | {subject}")
            return True
        except Exception as e:
            logger.error(f"Greška pri slanju emaila na {to}: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Dobrodošlica
    # ──────────────────────────────────────────────────────────────────────────
    def send_welcome(self, to: str, full_name: str) -> bool:
        name = full_name or to.split("@")[0]
        subject = "Dobrodošli u AI Sistem za učenje! 🎓"
        html = f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto">
          <h2 style="color:#6366f1">Zdravo, {name}!</h2>
          <p>Uspešno ste se registrovali u <strong>AI Sistem za učenje</strong>.</p>
          <p>Šta možete da radite:</p>
          <ul>
            <li>📄 Učitajte PDF dokumenta i prevedite ih AI-em</li>
            <li>🧠 Generišite kvizove automatski iz sadržaja</li>
            <li>📅 Kreirajte lični plan učenja</li>
            <li>📊 Pratite napredak kroz analitiku</li>
          </ul>
          <a href="http://localhost:5173" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold">
            Počnite sa učenjem →
          </a>
          <p style="margin-top:24px;color:#9ca3af;font-size:12px">AI Sistem za učenje</p>
        </div>
        """
        return self._send(to, subject, html)

    # ──────────────────────────────────────────────────────────────────────────
    # Dnevni podsetnik
    # ──────────────────────────────────────────────────────────────────────────
    def send_daily_reminder(
        self,
        to: str,
        full_name: str,
        today_quiz_titles: list[str],
        streak: int,
    ) -> bool:
        name = full_name or to.split("@")[0]
        subject = f"⏰ Podsetnik za danas — {len(today_quiz_titles)} kviz(a) te čeka"
        quiz_list_html = "".join(f"<li>{t}</li>" for t in today_quiz_titles) if today_quiz_titles else "<li><em>Nema zakazanih kvizova za danas</em></li>"
        streak_html = f'<p>🔥 Trenutni streak: <strong>{streak} dan{"a" if streak != 1 else ""}</strong> — ne prekidaj niz!</p>' if streak > 0 else ""
        html = f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto">
          <h2 style="color:#6366f1">Zdravo, {name}! 👋</h2>
          <p>Ovo je tvoj dnevni podsetnik za učenje.</p>
          {streak_html}
          <p><strong>Zakazani kvizovi za danas:</strong></p>
          <ul>{quiz_list_html}</ul>
          <a href="http://localhost:5173/quizzes" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold">
            Idi na kvizove →
          </a>
          <p style="margin-top:24px;color:#9ca3af;font-size:12px">Odjavite se od podsetnika u Podešavanjima → Plan učenja.</p>
        </div>
        """
        return self._send(to, subject, html)

    # ──────────────────────────────────────────────────────────────────────────
    # Nedeljni sažetak
    # ──────────────────────────────────────────────────────────────────────────
    def send_weekly_summary(
        self,
        to: str,
        full_name: str,
        week_completed: int,
        week_goal: int,
        avg_score: float,
        streak: int,
        best_quiz: Optional[str] = None,
    ) -> bool:
        name = full_name or to.split("@")[0]
        pct = round((week_completed / week_goal * 100) if week_goal else 0)
        achieved = week_completed >= week_goal
        subject = f"📊 Nedeljni izveštaj — {'Cilj postignut! 🎉' if achieved else f'{pct}% cilja'}"
        best_html = f"<p>🏆 Najbol kviz: <strong>{best_quiz}</strong></p>" if best_quiz else ""
        html = f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto">
          <h2 style="color:#6366f1">Nedeljni izveštaj, {name}</h2>
          <table style="width:100%;border-collapse:collapse;margin:16px 0">
            <tr><td style="padding:8px;background:#f9fafb;border-radius:4px">✅ Urađeni kvizovi</td><td style="padding:8px;font-weight:bold">{week_completed} / {week_goal}</td></tr>
            <tr><td style="padding:8px">📈 Prosečan score</td><td style="padding:8px;font-weight:bold">{avg_score}%</td></tr>
            <tr><td style="padding:8px;background:#f9fafb">🔥 Streak</td><td style="padding:8px;font-weight:bold">{streak} dana</td></tr>
          </table>
          {best_html}
          {"<p style='color:#10b981;font-weight:bold'>🎉 Bravo! Postigao si nedeljni cilj!</p>" if achieved else f"<p>Nedostaje još <strong>{week_goal - week_completed}</strong> kviz(a) do cilja.</p>"}
          <a href="http://localhost:5173/analytics" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold">
            Pogledaj analitiku →
          </a>
          <p style="margin-top:24px;color:#9ca3af;font-size:12px">AI Sistem za učenje</p>
        </div>
        """
        return self._send(to, subject, html)


    # ──────────────────────────────────────────────────────────────────────────
    # Reset lozinke
    # ──────────────────────────────────────────────────────────────────────────
    def send_password_reset(self, to: str, full_name: str, reset_link: str) -> bool:
        name = full_name or to.split("@")[0]
        subject = "🔑 Reset lozinke — AI Sistem za učenje"
        html = f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto">
          <h2 style="color:#6366f1">Reset lozinke, {name}</h2>
          <p>Primili smo zahtev za reset lozinke za tvoj nalog.</p>
          <p>Klikni na dugme ispod da postaviš novu lozinku. Link važi <strong>1 sat</strong>.</p>
          <a href="{reset_link}" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold">
            Resetuj lozinku →
          </a>
          <p style="margin-top:24px;color:#9ca3af;font-size:12px">
            Ako nisi tražio reset lozinke, ignoriši ovaj email. Nalog ostaje siguran.
          </p>
        </div>
        """
        return self._send(to, subject, html)


# Singleton
email_service = EmailService()
