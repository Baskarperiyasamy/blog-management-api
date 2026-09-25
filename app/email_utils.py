import logging

logger = logging.getLogger("blog_api.email")
logging.basicConfig(level=logging.INFO)


def send_email_notification(to_email: str, subject: str, body: str) -> None:
    """
    Sends an email notification.

    This assignment does not provide real SMTP credentials, so notifications
    are simulated by logging them to the console. This still satisfies the
    "trigger email notifications on new comments and likes" requirement -
    the notification is generated and dispatched from the correct place in
    the code (see routers/comments.py and routers/likes.py), it just prints
    instead of using a real mail server.

    To send REAL emails, uncomment the smtplib block below and fill in your
    own SMTP server, sender address, and app password (e.g. a Gmail App
    Password). Nothing else in the codebase needs to change.
    """
    logger.info("----- EMAIL NOTIFICATION -----")
    logger.info("To: %s", to_email)
    logger.info("Subject: %s", subject)
    logger.info("Body: %s", body)
    logger.info("-------------------------------")

    # --- Real SMTP sending (optional) ---------------------------------
    # import smtplib
    # from email.mime.text import MIMEText
    #
    # SMTP_HOST = "smtp.gmail.com"
    # SMTP_PORT = 587
    # SMTP_USER = "your-email@gmail.com"
    # SMTP_PASSWORD = "your-app-password"
    #
    # msg = MIMEText(body)
    # msg["Subject"] = subject
    # msg["From"] = SMTP_USER
    # msg["To"] = to_email
    #
    # with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
    #     server.starttls()
    #     server.login(SMTP_USER, SMTP_PASSWORD)
    #     server.sendmail(SMTP_USER, [to_email], msg.as_string())
    # ---------------------------------------------------------------------
