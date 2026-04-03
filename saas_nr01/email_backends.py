import json
import urllib.request
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class ResendBackend(BaseEmailBackend):
    """
    Custom Django Email Backend for Resend API using urllib (no dependencies).
    """
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', None)
        self.api_url = "https://api.resend.com/emails"

    def send_messages(self, email_messages):
        if not self.api_key:
            if not self.fail_silently:
                raise Exception("RESEND_API_KEY não configurada no settings.py")
            return 0

        sent_count = 0
        for message in email_messages:
            if self._send_api(message):
                sent_count += 1
        return sent_count

    def _send_api(self, message):
        try:
            # Resend API Payload
            payload = {
                "from": message.from_email,
                "to": message.to,
                "subject": message.subject,
                "html": message.body if message.content_subtype == 'html' else None,
                "text": message.body if message.content_subtype != 'html' else None,
            }
            
            # Se a mensagem tiver parte HTML (Django EmailMultiAlternatives)
            # Extrair o corpo HTML se existir
            if hasattr(message, 'alternatives') and message.alternatives:
                for content, mimetype in message.alternatives:
                    if mimetype == 'text/html':
                        payload['html'] = content
                        break

            # Limpar campos nulos
            payload = {k: v for k, v in payload.items() if v is not None}

            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(self.api_url, data=data)
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {self.api_key}')

            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if response.status in [200, 201]:
                    return True
                return False
        except Exception as e:
            if not self.fail_silently:
                raise e
            return False
