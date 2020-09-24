from pysendpulse.pysendpulse import PySendPulse


REST_API_ID = 'a1e29a8981861aa6795c007bab8d4e9b'
REST_API_SECRET = '9353d6de906c9f455efb7ae05334c489'


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
