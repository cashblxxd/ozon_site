from pysendpulse.pysendpulse import PySendPulse


REST_API_ID = '4531c6b62b81bc9b4810fcb56c8a5c5f'
REST_API_SECRET = '574cd5243163bee707008abb1a13fe88'


def send_join_mail(email, token):
    TOKEN_STORAGE = 'memcached'
    SPApiProxy = PySendPulse(REST_API_ID, REST_API_SECRET, TOKEN_STORAGE)
    email = {
        'subject': 'Подтверждение регистрации',
        'html': f'<p>Для подтверждения регистрации пройдите по ссылке: http://www.deepl.tech/confirm?token={token}</p>',
        'text': f'Для подтверждения регистрации пройдите по ссылке: http://www.deepl.tech/confirm?token={token}',
        'from': {'name': 'Команда deepl', 'email': 'service@deepl.tech'},
        'to': [
            {'name': f'"{email}"', 'email': email}
        ]
    }
    SPApiProxy.smtp_send_mail(email)
    print("Sent", email, token)


def send_reset_mail(email, token):
    TOKEN_STORAGE = 'memcached'
    SPApiProxy = PySendPulse(REST_API_ID, REST_API_SECRET, TOKEN_STORAGE)
    email = {
        'subject': 'Восстановление пароля',
        'html': f'<p>Для восстановления пароля пройдите по ссылке: http://www.deepl.tech/forgot?token={token}</p>',
        'text': f'Для восстановления пароля пройдите по ссылке: http://www.deepl.tech/forgot?token={token}',
        'from': {'name': 'Команда deepl', 'email': 'service@deepl.tech'},
        'to': [
            {'name': f'"{email}"', 'email': email}
        ]
    }
    SPApiProxy.smtp_send_mail(email)
    print("Sent", email, token)
