import os
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from backend.database.db_config import db

class EmailService:
    def __init__(self):
        # Retrieve credentials from environment variables
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        try:
            self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        except ValueError:
            self.smtp_port = 587
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')

    def send_report_email(self, user_id, analysis_id, recipient_email, recipient_name, summary, report_path):
        """
        Sends an email notification with the PDF report attached.
        Logs the status in the database.
        """
        if not recipient_email:
            print("[Email Service] Warning: No recipient email provided. Skipping email notification.")
            return False

        # Validate SMTP configuration
        if not self.smtp_user or not self.smtp_password:
            error_msg = "SMTP credentials (SMTP_USER/SMTP_PASSWORD) are not configured."
            print(f"[Email Service] Error: {error_msg}")
            self._log_email_status(user_id, analysis_id, recipient_email, 'FAILED', error_msg)
            return False

        # Construct Email Message
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = recipient_email
        msg['Subject'] = "Deepfake Analysis Report Generated"

        # Email body structure
        body = f"""Hello {recipient_name},

Your image analysis has been completed successfully.

Analysis Summary:
* Result: {summary.get('result', 'N/A')}
* Confidence Score: {summary.get('confidence', 0.0):.2f}%
* Trust Score: {summary.get('trust_score', 0)} / 100
* Analysis Date & Time: {summary.get('timestamp', 'N/A')}

Your report is ready and has been attached.

Thank you for using the Deepfake Detection System.
"""
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF Report
        attachment_filename = os.path.basename(report_path)
        attached_file_found = False

        if os.path.exists(report_path):
            try:
                with open(report_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {attachment_filename}",
                    )
                    msg.attach(part)
                    attached_file_found = True
            except Exception as e:
                print(f"[Email Service] Error reading attachment {report_path}: {e}")

        if not attached_file_found:
            error_msg = f"Failed to locate or open report attachment: {report_path}"
            print(f"[Email Service] Error: {error_msg}")
            self._log_email_status(user_id, analysis_id, recipient_email, 'FAILED', error_msg)
            return False

        # Connect and Send
        server = None
        try:
            print(f"[Email Service] Attempting to connect to {self.smtp_server}:{self.smtp_port}...")
            # Decide connection type based on port
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
                server.ehlo()
                # Check for STARTTLS compatibility
                if server.has_extn('STARTTLS'):
                    server.starttls()
                    server.ehlo()

            # Login and transmit message
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, recipient_email, msg.as_string())
            print(f"[Email Service] Successfully sent analysis report to {recipient_email}.")
            
            # Log success
            self._log_email_status(user_id, analysis_id, recipient_email, 'SENT')
            return True
        except Exception as e:
            tb = traceback.format_exc()
            error_msg = f"SMTP Transmission Exception: {str(e)}\n{tb}"
            print(f"[Email Service] Delivery failure: {error_msg}")
            
            # Log failure
            self._log_email_status(user_id, analysis_id, recipient_email, 'FAILED', error_msg)
            return False
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    def send_welcome_email(self, recipient_email, recipient_name):
        """
        Sends a registration confirmation welcome email to the user.
        """
        if not recipient_email or not self.smtp_user or not self.smtp_password:
            return False

        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = recipient_email
        msg['Subject'] = "AuraEye Registry: Auditor Provisioning Complete"

        body = f"""Hello {recipient_name},

Welcome to the Deepfake Detection System using Face and Corneal Reflection Analysis.

Your auditor node account has been registered successfully. You can now login using:
* Email: {recipient_email}

Start analyzing portrait uploads directly on your User Dashboard.

Best regards,
AuraEye Forensics Administration Team
"""
        msg.attach(MIMEText(body, 'plain'))

        server = None
        try:
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
                server.ehlo()
                if server.has_extn('STARTTLS'):
                    server.starttls()
                    server.ehlo()

            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, recipient_email, msg.as_string())
            print(f"[Email Service] Registration welcome email sent to {recipient_email}.")
            return True
        except Exception as e:
            print(f"[Email Service] Warning: Welcome email delivery failed: {e}")
            return False
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    def _log_email_status(self, user_id, analysis_id, email, status, error_message=None):
        """
        Inserts record to Email_Notifications table.
        """
        try:
            db.execute_query('''
                INSERT INTO Email_Notifications (user_id, analysis_id, email, delivery_status, error_message)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, analysis_id, email, status, error_message))
        except Exception as e:
            print(f"[Email Service] Database Logging Error: {e}")

email_service = EmailService()
