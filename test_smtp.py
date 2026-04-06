import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp():
    host = 'email-ssl.com.br'
    port = 465
    user = 'safeclima@nexttrust.com.br'
    password = 'Jb@36873021806'
    
    sender = 'SafeClima NR-01 <safeclima@nexttrust.com.br>'
    recipient = 'johnnybraga2@gmail.com'
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = 'Teste de SMTP Locaweb - SafeClima'
    
    body = "Este é um teste direto de conexão SMTP para verificar se o e-mail está funcionando."
    msg.attach(MIMEText(body, 'plain'))
    
    print(f"Conectando ao servidor SMTP {host}:{port}...")
    try:
        server = smtplib.SMTP_SSL(host, port, timeout=10)
        server.set_debuglevel(1)  # Mostra o log completo do SMTP
        print("Autenticando...")
        server.login(user, password)
        print("Enviando e-mail...")
        server.sendmail(user, recipient, msg.as_string())
        server.quit()
        print("E-mail enviado com SUCESSO!")
    except Exception as e:
        print("\n=== ERRO NO ENVIO DO E-MAIL ===")
        print(e)

if __name__ == '__main__':
    test_smtp()
