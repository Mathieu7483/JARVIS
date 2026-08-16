#!/usr/bin/env python3
"""
VERONICA — Agent spécialisé en gestion des emails et communications.
Personnalité : Professionnelle, discrète, efficace. Référence : Iron Man 3.
VERONICA gère les communications de Monsieur avec élégance et précision.
"""
import imaplib
import smtplib
import email
import os
import re
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from ollama import Client

load_dotenv()

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

IMAP_SERVER = "imap-mail.outlook.com"
IMAP_PORT   = 993
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT   = 587
ADDRESS     = os.getenv("OUTLOOK_ADDRESS", "")
PASSWORD    = os.getenv("OUTLOOK_PASSWORD", "")

VERONICA_SYSTEM = """Tu es VERONICA, agent de gestion des communications de JARVIS.
Tu gères les emails de Monsieur Mathieu avec professionnalisme et discrétion absolue.
Tu es élégante, précise et tu anticipes les besoins de Monsieur.

Tes règles absolues :
1. Tu résumes les emails de façon claire et hiérarchisée par importance.
2. Tu identifies les emails urgents ou nécessitant une action immédiate.
3. Tu signales les expéditeurs inconnus ou suspects.
4. Tu proposes des réponses adaptées au contexte et au ton de l'email.
5. Tu respectes la confidentialité absolue des communications.
6. Tes réponses sont en français, sans markdown, en phrases naturelles et formelles.
7. Tu commences par un résumé exécutif avant de détailler."""

class Veronica:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL

    def _appeler_ollama(self, prompt: str) -> str:
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": VERONICA_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.2, "num_predict": 600}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[VERONICA] Erreur connexion : {e}"

    def _decoder(self, valeur: str) -> str:
        if not valeur:
            return ""
        parties = decode_header(valeur)
        resultat = []
        for partie, encoding in parties:
            if isinstance(partie, bytes):
                try:
                    resultat.append(partie.decode(encoding or 'utf-8', errors='replace'))
                except Exception:
                    resultat.append(partie.decode('latin-1', errors='replace'))
            else:
                resultat.append(str(partie))
        return " ".join(resultat).strip()

    def _connecter_imap(self):
        """Ouvre une connexion IMAP."""
        if not ADDRESS or not PASSWORD:
            raise ValueError("Identifiants Outlook manquants dans le fichier .env")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(ADDRESS, PASSWORD)
        return mail

    def _extraire_corps(self, msg) -> str:
        """Extrait le corps texte d'un email."""
        corps = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        corps = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except Exception:
                        pass
        else:
            try:
                corps = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            except Exception:
                corps = ""
        return corps[:1000].strip()

    def lire_emails(self, max_emails: int = 5, non_lus_seulement: bool = True) -> str:
        """Récupère et analyse les derniers emails."""
        try:
            print(f"[VERONICA] Connexion à {IMAP_SERVER}...")
            mail = self._connecter_imap()
            mail.select("INBOX")

            if non_lus_seulement:
                status, messages = mail.search(None, "UNSEEN")
                ids = messages[0].split()
                mode = "non lus"
            else:
                status, messages = mail.search(None, "ALL")
                ids = messages[0].split()
                mode = "récents"

            if not ids:
                mail.logout()
                return f"[VERONICA] Aucun email {mode} dans la boîte de réception, Monsieur."

            ids_a_lire = ids[-max_emails:]
            print(f"[VERONICA] {len(ids_a_lire)} email(s) {mode} trouvé(s).")

            rapport = f"RAPPORT VERONICA — {len(ids_a_lire)} email(s) {mode} :\n\n"
            emails_data = []

            for uid in reversed(ids_a_lire):
                status, data = mail.fetch(uid, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                exp   = self._decoder(msg.get("From", "Inconnu"))
                sujet = self._decoder(msg.get("Subject", "Sans sujet"))
                date  = self._decoder(msg.get("Date", ""))
                corps = self._extraire_corps(msg)
                emails_data.append({
                    "expediteur": exp, "sujet": sujet,
                    "date": date, "corps": corps
                })
                rapport += f"DE : {exp}\nSUJET : {sujet}\nDATE : {date}\nEXTRAIT : {corps[:300]}\n{'-'*40}\n"

            mail.logout()

            prompt = (
                f"Voici les emails de Monsieur ({mode}). "
                "Fais un résumé exécutif, identifie les urgences et les actions requises :\n\n" + rapport
            )
            return self._appeler_ollama(prompt)

        except imaplib.IMAP4.error as e:
            return f"[VERONICA] Erreur d'authentification : {e}. Vérifiez les identifiants dans le fichier .env"
        except Exception as e:
            return f"[VERONICA] Erreur de connexion : {e}"

    def compter_emails(self) -> str:
        """Compte les emails non lus."""
        try:
            mail = self._connecter_imap()
            mail.select("INBOX")
            status, messages = mail.search(None, "UNSEEN")
            nb = len(messages[0].split()) if messages[0] else 0
            mail.logout()
            if nb == 0:
                return "Aucun email non lu dans votre boîte de réception, Monsieur."
            return f"Monsieur a {nb} email(s) non lu(s) en attente."
        except Exception as e:
            return f"[VERONICA] Impossible de compter les emails : {e}"

    def rediger_reponse(self, contexte_email: str, instructions: str = "") -> str:
        """Rédige une réponse à un email selon les instructions de Monsieur."""
        prompt = (
            f"Rédige une réponse professionnelle et élégante à cet email pour Monsieur Mathieu.\n"
            f"Email reçu :\n{contexte_email}\n\n"
            f"Instructions de Monsieur : {instructions if instructions else 'Réponse standard polie.'}\n\n"
            "La réponse doit être formelle, concise et parfaitement rédigée en français."
        )
        return self._appeler_ollama(prompt)

    def analyser_spam(self) -> str:
        """Analyse la boîte spam/courrier indésirable."""
        try:
            mail = self._connecter_imap()
            dossiers_spam = ['Junk', 'Spam', 'Junk Email', 'Courrier indésirable']
            for dossier in dossiers_spam:
                try:
                    mail.select(f'"{dossier}"')
                    status, messages = mail.search(None, "ALL")
                    nb = len(messages[0].split()) if messages[0] else 0
                    if nb > 0:
                        mail.logout()
                        return f"[VERONICA] {nb} email(s) dans le dossier spam '{dossier}', Monsieur."
                except Exception:
                    continue
            mail.logout()
            return "[VERONICA] Dossier spam introuvable ou vide, Monsieur."
        except Exception as e:
            return f"[VERONICA] Erreur analyse spam : {e}"

    def executer(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal."""
        tache_lower = tache.lower()

        # Compter les emails
        if any(m in tache_lower for m in ['combien', 'compte', 'nombre']):
            return self.compter_emails()

        # Spam
        if any(m in tache_lower for m in ['spam', 'indésirable', 'junk']):
            return self.analyser_spam()

        # Rédiger une réponse
        if any(m in tache_lower for m in ['réponds', 'rédige', 'écris', 'réponse']):
            return self.rediger_reponse(contexte or tache)

        # Lire tous les emails (pas seulement non lus)
        if any(m in tache_lower for m in ['tous', 'récents', 'derniers']):
            return self.lire_emails(non_lus_seulement=False)

        # Lecture par défaut — non lus
        return self.lire_emails()
