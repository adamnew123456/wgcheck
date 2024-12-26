#!/usr/bin/env
# Send alert email using your favorite SMTP client
from email.mime.text import MIMEText
import html
import smtplib

message = "<pre>" + html.escape(message_text) + "</pre>"
message = MIMEText(message, "html", "utf-8")
message["Subject"] = f"Alert: {title}"
message["From"] = user
message["To"] = rcpt

server = smtplib.SMTP_SSL(srvr, port)
server.login(user, pswd)
server.sendmail(user, [rcpt], message.as_string())
server.quit()
