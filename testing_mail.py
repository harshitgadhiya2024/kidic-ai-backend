import smtplib
from email.mime.text import MIMEText

msg = MIMEText("SMTP is working 🚀")
msg["Subject"] = "Test Mail"
msg["From"] = "info@nehodating.com"
msg["To"] = "harshitgadhiya8980@gmail.com"

server = smtplib.SMTP("smtpout.secureserver.net", 587)
server.starttls()
server.login("info@nehodating.com", "Sunking1313@")
server.send_message(msg)
server.quit()

print("✅ Email sent successfully")
