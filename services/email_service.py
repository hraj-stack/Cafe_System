"""
services/email_service.py
─────────────────────────
Centralised email delivery for HRD Cafe.

Usage:
    from services.email_service import send_email

    ok, err = send_email(
        to      = "customer@example.com",
        subject = "Your Reservation Confirmation",
        html    = "<h1>Hello!</h1>",
    )
    if not ok:
        # err is a user-friendly string, safe to show in the UI
        flash(err, "danger")

Configuration (in .env):
    MAIL_HOST       = smtp.gmail.com
    MAIL_PORT       = 587
    MAIL_USERNAME   = your-address@gmail.com
    MAIL_PASSWORD   = your-16-char-app-password
    MAIL_FROM_NAME  = HRD Cafe
    MAIL_FROM_EMAIL = your-address@gmail.com
"""

import os
import smtplib
import threading
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr


# ── helpers ──────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def _valid_email(addr: str) -> bool:
    return bool(_EMAIL_RE.match(addr.strip()))


def _get_cfg():
    """Read mail settings — prefer app.config, fall back to env vars."""
    try:
        from flask import current_app
        cfg = current_app.config
        return {
            'host':       cfg.get('MAIL_HOST', 'smtp.gmail.com'),
            'port':       int(cfg.get('MAIL_PORT', 587)),
            'username':   cfg.get('MAIL_USERNAME', ''),
            'password':   cfg.get('MAIL_PASSWORD', ''),
            'from_name':  cfg.get('MAIL_FROM_NAME', 'HRD Cafe'),
            'from_email': cfg.get('MAIL_FROM_EMAIL', ''),
        }
    except RuntimeError:
        # Outside app context — read directly from env
        return {
            'host':       os.environ.get('MAIL_HOST', 'smtp.gmail.com'),
            'port':       int(os.environ.get('MAIL_PORT', 587)),
            'username':   os.environ.get('MAIL_USERNAME', ''),
            'password':   os.environ.get('MAIL_PASSWORD', ''),
            'from_name':  os.environ.get('MAIL_FROM_NAME', 'HRD Cafe'),
            'from_email': os.environ.get('MAIL_FROM_EMAIL', ''),
        }


def _log_to_db(recipient, subject, body, status):
    """Persist a send attempt to MessageLog (best-effort, never raises)."""
    try:
        from models import db
        from models.message_log import MessageLog
        log = MessageLog(
            recipient=recipient,
            message_type='Email',
            subject=subject,
            body=body,
            status=status,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        print(f"[EmailService] DB log failed: {exc}")


# ── core delivery ─────────────────────────────────────────────────────────────

def _do_send(to: str, subject: str, html: str) -> tuple[bool, str | None]:
    """
    Synchronous send.  Returns (True, None) on success or (False, user_msg).
    """
    cfg = _get_cfg()

    if not cfg['username'] or not cfg['password']:
        msg = "Email service is not configured. Please contact the administrator."
        print("[EmailService] MAIL_USERNAME / MAIL_PASSWORD not set in .env")
        _log_to_db(to, subject, html, 'Failed')
        return False, msg

    if not _valid_email(to):
        return False, "Invalid recipient email address."

    from_addr = formataddr((cfg['from_name'], cfg['from_email'] or cfg['username']))

    mime = MIMEMultipart('alternative')
    mime['Subject'] = subject
    mime['From']    = from_addr
    mime['To']      = to
    mime.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        port = cfg['port']
        if port == 465:
            # SSL
            with smtplib.SMTP_SSL(cfg['host'], port, timeout=10) as server:
                server.login(cfg['username'], cfg['password'])
                server.send_message(mime)
        else:
            # STARTTLS (587 or 25)
            with smtplib.SMTP(cfg['host'], port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(cfg['username'], cfg['password'])
                server.send_message(mime)

        print(f"[EmailService] ✓ Email sent → {to} | {subject}")
        _log_to_db(to, subject, html, 'Sent')
        return True, None

    except smtplib.SMTPAuthenticationError:
        print("[EmailService] Authentication failed — check MAIL_USERNAME / MAIL_PASSWORD in .env")
        _log_to_db(to, subject, html, 'Failed')
        return False, "Unable to send email right now. Please try again later."

    except Exception as exc:
        print(f"[EmailService] Send failed: {exc}")
        _log_to_db(to, subject, html, 'Failed')
        return False, "Unable to send email right now. Please try again later."


# ── public API ────────────────────────────────────────────────────────────────

def send_email(to: str, subject: str, html: str) -> tuple[bool, str | None]:
    """
    Send an HTML email synchronously.

    Returns:
        (True, None)          — email delivered successfully
        (False, "user msg")   — delivery failed, message safe to show in UI
    """
    return _do_send(to, subject, html)


def send_email_async(to: str, subject: str, html: str) -> None:
    """
    Fire-and-forget email send in a background thread.
    Use this inside Flask routes to avoid blocking the response.
    Errors are printed to console and logged to DB — not raised.
    """
    from flask import current_app
    # Capture the app so the thread has an application context
    app = current_app._get_current_object()

    def _worker():
        with app.app_context():
            _do_send(to, subject, html)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
