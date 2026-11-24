"""Notification e-mail à Matech à chaque nouvelle commande."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from outils import fcfa, secret


def envoyer_email_notification(nom, contact, type_pave, surface, montant_total, zone, numero):
    """Secrets à configurer dans Streamlit Cloud (App settings > Secrets) :
         EMAIL_ADDRESS = "matech.contacts@gmail.com"
         EMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"   (mot de passe d'application Gmail)
       Sans ces secrets, aucun e-mail n'est envoyé mais la commande est bien enregistrée."""
    try:
        expediteur = secret("EMAIL_ADDRESS") or config.EMAIL_CONTACT
        mot_de_passe = secret("EMAIL_APP_PASSWORD")
        if not mot_de_passe:
            return False
        msg = MIMEMultipart()
        msg["From"] = expediteur
        msg["To"] = config.EMAIL_CONTACT
        msg["Subject"] = f"Commande {numero} — {nom}"
        corps = (f"Nouvelle commande ST-Ecoparvis !\n\nN° commande : {numero}\nClient : {nom}\n"
                 f"Contact : {contact}\nType : {type_pave}\nSurface : {surface} m²\n"
                 f"Zone : {zone}\nMontant : {fcfa(montant_total)}\n\n— ST-Ecoparvis")
        msg.attach(MIMEText(corps, "plain", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as serveur:
            serveur.starttls()
            serveur.login(expediteur, mot_de_passe)
            serveur.sendmail(expediteur, config.EMAIL_CONTACT, msg.as_string())
        return True
    except Exception:
        return False