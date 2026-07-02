#!/usr/bin/env python3
import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = "imap-mail.outlook.com"
IMAP_PORT   = 993
ADDRESS     = os.getenv("OUTLOOK_ADDRESS", "")
PASSWORD    = os.getenv("OUTLOOK_PASSWORD", "")

def _decoder(valeur):
    """Décode proprement les headers email (UTF-8, latin-1, etc.)."""
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

def recuperer_derniers_emails(max_emails: int = 5) -> str:
    """
    Se connecte à Outlook/Hotmail via IMAP et récupère les derniers emails non lus.
    Retourne un résumé formaté pour VERONICA.
    """
    if not ADDRESS or not PASSWORD:
        return "Erreur : Identifiants Outlook manquants dans le fichier .env"

    try:
        print(f"[VERONICA] Connexion à {IMAP_SERVER}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(ADDRESS, PASSWORD)
        mail.select("INBOX")

        # Cherche les emails non lus
        status, messages = mail.search(None, "UNSEEN")
        ids_non_lus = messages[0].split()

        if not ids_non_lus:
            # Si pas de non lus, prend les derniers reçus
            status, messages = mail.search(None, "ALL")
            tous_ids = messages[0].split()
            ids_a_lire = tous_ids[-max_emails:] if len(tous_ids) >= max_emails else tous_ids
            mode = "derniers reçus"
        else:
            ids_a_lire = ids_non_lus[-max_emails:]
            mode = "non lus"

        print(f"[VERONICA] {len(ids_a_lire)} emails {mode} trouvés.")

        if not ids_a_lire:
            return "Aucun e-mail reçu. Flux vide."

        rapport = f"RAPPORT VERONICA — {len(ids_a_lire)} e-mail(s) {mode} :\n\n"

        for i, uid in enumerate(reversed(ids_a_lire), 1):
            status, data = mail.fetch(uid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            expediteur = _decoder(msg.get("From", "Inconnu"))
            sujet      = _decoder(msg.get("Subject", "Sans sujet"))
            date       = _decoder(msg.get("Date", "Date inconnue"))

            # Extrait le corps du message
            corps = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            corps = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            corps = corps[:300].strip()
                            break
                        except Exception:
                            pass
            else:
                try:
                    corps = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                    corps = corps[:300].strip()
                except Exception:
                    corps = "Corps non lisible."

            rapport += f"E-MAIL {i} :\n"
            rapport += f"De      : {expediteur}\n"
            rapport += f"Sujet   : {sujet}\n"
            rapport += f"Date    : {date}\n"
            rapport += f"Extrait : {corps}\n"
            rapport += "-" * 40 + "\n"

        mail.logout()
        return rapport

    except imaplib.IMAP4.error as e:
        return f"Erreur d'authentification IMAP : {str(e)}"
    except Exception as e:
        return f"Erreur de connexion à la boîte mail : {str(e)}"