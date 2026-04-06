import requests

def test_password_reset():
    url = "https://safeclima.com.br/accounts/password-reset/"
    session = requests.Session()
    
    try:
        # Step 1: Get the form to retrieve the CSRF token
        response = session.get(url, timeout=10)
        
        # Check if we can reach the server
        if response.status_code != 200:
            print(f"Erro ao acessar {url}: {response.status_code}")
            return
            
        # Extract CSRF token from HTML body
        csrf_token = None
        html = response.text
        if 'name="csrfmiddlewaretoken" value="' in html:
            parts = html.split('name="csrfmiddlewaretoken" value="')
            if len(parts) > 1:
                csrf_token = parts[1].split('"')[0]
                
        if not csrf_token:
            print("Não foi possível obter o token CSRF.")
            return
            
        print("Obteve token CSRF com sucesso")
        
        # Add CSRF token to cookies so the server accepts it
        session.cookies.set('csrftoken', csrf_token, domain='safeclima.com.br')
        
        # Step 2: Post the email to trigger the password reset
        data = {
            "email": "johnny.oliveira@sp.senai.br",
            "csrfmiddlewaretoken": csrf_token
        }
        headers = {
            "Referer": url
        }
        
        post_response = session.post(url, data=data, headers=headers)
        
        # We expect a redirect or a 200 OK after successful post
        if post_response.status_code in [200, 302]:
            print(f"Sucesso! Formulário de reset enviado com status: {post_response.status_code}")
        else:
            print(f"Falha ao enviar o formulário. Status: {post_response.status_code}")
            print(post_response.text[:500])
            
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com o servidor de produção: {e}")

if __name__ == "__main__":
    test_password_reset()
