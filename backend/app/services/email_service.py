# -*- coding: utf-8 -*-
"""
AI Learning System
Email Service
Verzija: 1.0.0
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
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
            logger.warning("Email nije konfigurisan - preskacem slanje.")
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
            logger.error(f"Greska pri slanju emaila na {to}: {e}")
            return False

    def send_welcome(self, to: str, full_name: str) -> bool:
        name = full_name or to.split("@")[0]
        subject = "Dobrodosli u AI Sistem za ucenje!"
        html = "<div style='font-family:sans-serif;max-width:560px;margin:0 auto'>"
        html += f"<h2 style='color:#6366f1'>Zdravo, {name}!</h2>"
        html += (
            "<p>Uspesno ste se registrovali u <strong>AI Sistem za ucenje</strong>.</p>"
        )
        html += "<p>Sta mozete da radite:</p>"
        html += "<ul>"
        html += "<li>Ucitajte PDF dokumenta i prevedite ih AI-em</li>"
        html += "<li>Generisite kvizove automatski iz sadrzaja</li>"
        html += "<li>Kreirajte licni plan ucenja</li>"
        html += "<li>Pratite napredak kroz analitiku</li>"
        html += "</ul>"
        html += "<a href='http://localhost:5173' style='display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold'>Pocnite sa ucenjem</a>"  # noqa: E501
        html += "<p style='margin-top:24px;color:#9ca3af;font-size:12px'>AI Sistem za ucenje</p></div>"
        return self._send(to, subject, html)

    def send_daily_reminder(
        self,
        to: str,
        full_name: str,
        today_quiz_titles: list,
        streak: int,
    ) -> bool:
        name = full_name or to.split("@")[0]
        subject = f"Podsetnik za danas - {len(today_quiz_titles)} kviz(eva) te ceka"
        quiz_list_html = (
            "".join(f"<li>{t}</li>" for t in today_quiz_titles)
            if today_quiz_titles
            else "<li><em>Nema zakazanih kvizova za danas</em></li>"
        )
        streak_html = (
            f"<p>Trenutni streak: <strong>{streak} dan</strong> - ne prekidaj niz!</p>"
            if streak > 0
            else ""
        )
        html = "<div style='font-family:sans-serif;max-width:560px;margin:0 auto'>"
        html += f"<h2 style='color:#6366f1'>Zdravo, {name}!</h2>"
        html += "<p>Ovo je tvoj dnevni podsetnik za ucenje.</p>"
        html += streak_html
        html += "<p><strong>Zakazani kvizovi za danas:</strong></p>"
        html += f"<ul>{quiz_list_html}</ul>"
        html += "<a href='http://localhost:5173/quizzes' style='display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold'>Idi na kvizove</a>"  # noqa: E501
        html += "<p style='margin-top:24px;color:#9ca3af;font-size:12px'>Odjavite se od podsetnika u Podesavanjima.</p></div>"  # noqa: E501
        return self._send(to, subject, html)

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
        subject = (
            f"Nedeljni izvestaj - {'Cilj postignut!' if achieved else f'{pct}% cilja'}"
        )
        best_html = (
            f"<p>Najbolji kviz: <strong>{best_quiz}</strong></p>" if best_quiz else ""
        )
        html = "<div style='font-family:sans-serif;max-width:560px;margin:0 auto'>"
        html += f"<h2 style='color:#6366f1'>Nedeljni izvestaj, {name}</h2>"
        html += "<table style='width:100%;border-collapse:collapse;margin:16px 0'>"
        html += f"<tr><td style='padding:8px;background:#f9fafb;border-radius:4px'>Uradjeni kvizovi</td><td style='padding:8px;font-weight:bold'>{week_completed} / {week_goal}</td></tr>"  # noqa: E501
        html += f"<tr><td style='padding:8px'>Prosecan score</td><td style='padding:8px;font-weight:bold'>{avg_score}%</td></tr>"  # noqa: E501
        html += f"<tr><td style='padding:8px;background:#f9fafb'>Streak</td><td style='padding:8px;font-weight:bold'>{streak} dana</td></tr>"  # noqa: E501
        html += "</table>"
        html += best_html
        if achieved:
            html += "<p style='color:#10b981;font-weight:bold'>Bravo! Postigao si nedeljni cilj!</p>"
        else:
            html += f"<p>Nedostaje jos <strong>{week_goal - week_completed}</strong> kviz(eva) do cilja.</p>"
        html += "<a href='http://localhost:5173/analytics' style='display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold'>Pogledaj analitiku</a>"  # noqa: E501
        html += "<p style='margin-top:24px;color:#9ca3af;font-size:12px'>AI Sistem za ucenje</p></div>"
        return self._send(to, subject, html)

    def send_password_reset(self, to: str, full_name: str, reset_link: str) -> bool:
        name = full_name or to.split("@")[0]
        subject = "Reset lozinke - AI Sistem za ucenje"
        html = "<div style='font-family:sans-serif;max-width:560px;margin:0 auto'>"
        html += f"<h2 style='color:#6366f1'>Reset lozinke, {name}</h2>"
        html += "<p>Primili smo zahtev za reset lozinke za tvoj nalog.</p>"
        html += "<p>Klikni na dugme ispod da postavis novu lozinku. Link vazi <strong>1 sat</strong>.</p>"
        html += f"<a href='{reset_link}' style='display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold'>Resetuj lozinku</a>"  # noqa: E501
        html += "<p style='margin-top:24px;color:#9ca3af;font-size:12px'>Ako nisi trazio reset lozinke, ignorisi ovaj email. Nalog ostaje siguran.</p></div>"  # noqa: E501
        return self._send(to, subject, html)

    def send_document_processed(
        self,
        to: str,
        full_name: str,
        document_title: str,
        total_pages: int,
        total_chunks: int,
    ) -> bool:
        name = full_name or to.split("@")[0]
        subject = f"Dokument obradjen - {document_title}"
        html = "<div style='font-family:sans-serif;max-width:560px;margin:0 auto'>"
        html += f"<h2 style='color:#10b981'>Dokument je spreman, {name}!</h2>"
        html += f"<p>Vas dokument <strong>{document_title}</strong> je uspesno obradjen.</p>"
        html += "<table style='width:100%;border-collapse:collapse;margin:16px 0'>"
        html += f"<tr><td style='padding:8px;background:#f9fafb;border-radius:4px'>Stranica</td><td style='padding:8px;font-weight:bold'>{total_pages}</td></tr>"  # noqa: E501
        html += f"<tr><td style='padding:8px'>Chunk-ova</td><td style='padding:8px;font-weight:bold'>{total_chunks}</td></tr>"  # noqa: E501
        html += "</table>"
        html += "<p>Sada mozete:</p><ul>"
        html += "<li>Prevesti dokument na drugi jezik</li>"
        html += "<li>Generisati kviz iz sadrzaja</li>"
        html += "<li>Koristiti dokument za RAG pretragu</li></ul>"
        html += "<a href='http://localhost:5173/documents' style='display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold'>Pogledaj dokumente</a></div>"  # noqa: E501
        return self._send(to, subject, html)

    def send_quiz_completed(
        self,
        to: str,
        full_name: str,
        quiz_title: str,
        score: int,
        total: int,
        passed: bool,
    ) -> bool:
        name = full_name or to.split("@")[0]
        pct = round((score / total * 100) if total else 0)
        subject = f"Kviz zavrsen - {quiz_title}: {pct}%"
        html = "<div style='font-family:sans-serif;max-width:560px;margin:0 auto'>"
        html += f"<h2 style='color:{'#10b981' if passed else '#ef4444'}'>{'Bravo!' if passed else 'Nisi prosao'}</h2>"
        html += f"<p>{name}, zavrsili ste kviz <strong>{quiz_title}</strong>.</p>"
        html += f"<p>Rezultat: <strong>{score}/{total}</strong> ({pct}%)</p>"
        if passed:
            html += "<p style='color:#10b981;font-weight:bold'>Prosli ste kviz!</p>"
        else:
            html += f"<p>Niste prosli. Potrebno je <strong>{pct}%</strong> za prolaz. Pokusajte ponovo!</p>"
        html += "<a href='http://localhost:5173/quizzes' style='display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold'>Pogledaj kvizove</a></div>"  # noqa: E501
        return self._send(to, subject, html)

    def send_chunks_ready(
        self,
        to: str,
        full_name: str,
        document_title: str,
        total_chunks: int,
        total_pages: int,
    ) -> bool:
        """
        Šalje email kada su chunk-ovi uspešno kreirani.

        Args:
            to: Email adresa primaoca
            full_name: Ime korisnika
            document_title: Naslov dokumenta
            total_chunks: Broj kreiranih chunk-ova
            total_pages: Broj stranica dokumenta
        """
        name = full_name or to.split("@")[0]
        subject = f"Odlomci dokumenta spremni - {document_title}"
        html = "<div style='font-family:sans-serif;max-width:560px;margin:0 auto'>"
        html += f"<h2 style='color:#10b981'>Odlomci su spremni, {name}!</h2>"
        html += (
            f"<p>Vaš dokument <strong>{document_title}</strong> je uspešno obrađen.</p>"
        )
        html += "<table style='width:100%;border-collapse:collapse;margin:16px 0'>"
        html += f"<tr><td style='padding:8px;background:#f9fafb;border-radius:4px'>Stranica</td><td style='padding:8px;font-weight:bold'>{total_pages}</td></tr>"  # noqa: E501
        html += f"<tr><td style='padding:8px'>Odlomaka (chunk-ova)</td><td style='padding:8px;font-weight:bold'>{total_chunks}</td></tr>"  # noqa: E501
        html += "</table>"
        html += "<p>Sada možete:</p><ul>"
        html += "<li>Prevesti dokument na drugi jezik</li>"
        html += "<li>Generisati kviz iz sadržaja</li>"
        html += "<li>Koristiti dokument za RAG pretragu</li></ul>"
        html += "<a href='http://localhost:5173/documents' style='display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold'>Pogledaj dokumente</a>"  # noqa: E501
        html += "<p style='margin-top:24px;color:#9ca3af;font-size:12px'>Započnite novi zadatak ili se izlogujte. Agent će vas obavestiti putem email-a kada završi.</p></div>"  # noqa: E501
        return self._send(to, subject, html)

    def send_translation_ready(
        self,
        to: str,
        full_name: str,
        document_title: str,
        source_language: str,
        target_language: str,
        total_chunks: int,
    ) -> bool:
        """
        Šalje email kada je prevod dokumenta završen.

        Args:
            to: Email adresa primaoca
            full_name: Ime korisnika
            document_title: Naslov dokumenta
            source_language: Izvorni jezik
            target_language: Ciljni jezik
            total_chunks: Broj prevedenih chunk-ova
        """
        name = full_name or to.split("@")[0]
        subject = f"Prevod dokumenta završen - {document_title}"

        # Mapiranje jezičkih kodova u imena
        lang_names = {
            "en": "English",
            "sr": "Serbian",
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "pt": "Portuguese",
            "nl": "Dutch",
            "pl": "Polish",
            "hu": "Hungarian",
        }
        src_name = lang_names.get(source_language, source_language)
        tgt_name = lang_names.get(target_language, target_language)

        html = "<div style='font-family:sans-serif;max-width:560px;margin:0 auto'>"
        html += f"<h2 style='color:#10b981'>Prevod je završen, {name}!</h2>"
        html += f"<p>Vaš dokument <strong>{document_title}</strong> je uspešno preveden.</p>"
        html += "<table style='width:100%;border-collapse:collapse;margin:16px 0'>"
        html += f"<tr><td style='padding:8px;background:#f9fafb;border-radius:4px'>Iz jezika</td><td style='padding:8px;font-weight:bold'>{src_name}</td></tr>"  # noqa: E501
        html += f"<tr><td style='padding:8px'>Na jezik</td><td style='padding:8px;font-weight:bold'>{tgt_name}</td></tr>"  # noqa: E501
        html += f"<tr><td style='padding:8px;background:#f9fafb'>Prevedenih odlomaka</td><td style='padding:8px;font-weight:bold'>{total_chunks}</td></tr>"  # noqa: E501
        html += "</table>"
        html += "<p>Sada možete:</p><ul>"
        html += "<li>Generisati kviz iz prevedenog sadržaja</li>"
        html += "<li>Pretraživati prevedeni sadržaj</li>"
        html += "<li>Pogledati dokument</li></ul>"
        html += "<a href='http://localhost:5173/documents' style='display:inline-block;margin-top:16px;padding:12px 24px;background:#6366f1;color:white;border-radius:8px;text-decoration:none;font-weight:bold'>Pogledaj dokumente</a>"  # noqa: E501
        html += "<p style='margin-top:24px;color:#9ca3af;font-size:12px'>Započnite novi zadatak ili se izlogujte. Agent će vas obavestiti putem email-a kada završi.</p></div>"  # noqa: E501
        return self._send(to, subject, html)


email_service = EmailService()
