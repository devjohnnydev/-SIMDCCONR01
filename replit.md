# SaaS NR-01 - Plataforma de Gestao de Riscos Ocupacionais

## Visao Geral

Plataforma multi-tenant B2B para conformidade trabalhista brasileira (NR-01), avaliacao de clima organizacional e acompanhamento de bem-estar de funcionarios. Gera relatorios PDF com qualidade de auditoria para pericia judicial, com conformidade LGPD completa.

## Stack Tecnologica

- **Backend**: Django 5.x + Django REST Framework
- **Banco de Dados**: PostgreSQL (Neon)
- **Frontend**: Bootstrap 5 + Crispy Forms
- **Servidor**: Gunicorn + WhiteNoise
- **PDF**: WeasyPrint

## Estrutura do Projeto

```
/
├── saas_nr01/           # Configuracoes Django
│   ├── settings.py      # Configuracoes principais
│   ├── urls.py          # URLs raiz
│   └── wsgi.py          # WSGI entry point
├── accounts/            # Autenticacao e usuarios
│   ├── models.py        # User customizado (email-based)
│   └── views.py         # Login, signup, dashboards
├── companies/           # Gestao de empresas
│   ├── models.py        # Company, Announcement
│   ├── middleware.py    # CompanyMiddleware
│   └── context_processors.py  # Branding dinamico
├── employees/           # Gestao de funcionarios
│   ├── models.py        # Employee, ImportLog
│   └── views.py         # CRUD, importacao CSV
├── forms_builder/       # Sistema de formularios
│   ├── models.py        # Template, Question, Instance, Answer
│   └── views.py         # Templates, formularios, respostas
├── reports/             # Relatorios e dashboards
│   ├── models.py        # Report
│   └── views.py         # Dashboard, geracao PDF
├── billing/             # Planos e assinaturas
│   └── models.py        # Plan, Subscription
├── audit/               # Logs de auditoria LGPD
│   └── models.py        # AuditLog
└── templates/           # Templates HTML
    ├── base.html        # Layout base com branding
    └── [app]/           # Templates por app
```

## Credenciais de Acesso

### Admin Master (Plataforma)
- Email: admin@saas.com
- Senha: admin123

## Funcionalidades Principais

### Papeis de Usuario
1. **ADMIN_MASTER**: Administrador da plataforma (aprova empresas)
2. **COMPANY_ADMIN**: Administrador da empresa (cria formularios)
3. **EMPLOYEE**: Funcionario (responde formularios)

### Workflow de Empresa
1. Cadastro publico → Status PENDING
2. ADMIN_MASTER aprova → Status ACTIVE
3. COMPANY_ADMIN cria funcionarios e formularios

### Templates de Formulario
- **NR-01**: Riscos psicossociais ocupacionais
- **Clima Organizacional**: Engajamento e lideranca
- **Bem-estar**: Saude mental e fisica

### Tipos de Perguntas
- Escala Likert (1-5, 1-10)
- Sim/Nao
- Multipla escolha
- Texto aberto
- Data, Numero

### Relatorios PDF
- Qualidade de auditoria/pericia
- Branding da empresa
- Metodologia documentada
- Espaco para parecer tecnico

## Comandos Uteis

```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Dados iniciais (planos, templates, admin)
python manage.py setup_initial_data

# Coletar estaticos
python manage.py collectstatic --no-input

# Servidor de desenvolvimento
python manage.py runserver 0.0.0.0:5000

# Producao
gunicorn --bind 0.0.0.0:5000 saas_nr01.wsgi:application
```

## Variaveis de Ambiente

- `DATABASE_URL`: URL de conexao PostgreSQL
- `SESSION_SECRET`: Chave secreta Django
- `DEBUG`: True/False para modo debug

## Proximos Passos

- [ ] Integrar pagamentos (Stripe)
- [ ] Notificacoes por email
- [ ] API REST completa
- [ ] Dashboard com graficos avancados
- [ ] Export de dados LGPD

## Alteracoes Recentes

- **2024-12-04**: Redesign completo da interface
  - Novo design profissional com fonte Inter
  - Paleta de cores moderna com gradientes
  - Sidebar escura com navegacao aprimorada
  - Cards com sombras e hover effects
  - Formularios com melhor UX
  - Paginas de login e cadastro redesenhadas
  - Dashboards com metricas visuais melhoradas
  - Empty states informativos

- **2024-12**: Projeto inicial criado
  - Modelos de dados completos
  - Sistema de autenticacao por email
  - Middleware de branding dinamico
  - Templates de formularios NR-01, Clima, Bem-estar
  - Geracao de PDF com WeasyPrint
  - Auditoria LGPD
