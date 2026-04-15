# SIMDCCONR01 — Sistema de Compliance NR-01, NR-17 e NR-12

![SIMDCCONR01 Banner](https://img.shields.io/badge/Status-Project_Completed-success?style=for-the-badge&logo=django)
![Compliance](https://img.shields.io/badge/Compliance-NR--01%20|%20NR--17%20|%20NR--12-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)

O **SIMDCCONR01** é uma plataforma SaaS (Software as a Service) de alta performance projetada para a gestão de conformidade em Saúde e Segurança do Trabalho (SST). O sistema integra medições psicossociais, neurocognitivas e ergonômicas, gerando laudos periciais determinísticos e auditáveis para atender às exigências das Normas Regulamentadoras brasileiras (Portaria MTE 1.419/2024).

---

## 🚀 Funcionalidades Principais!!!

### 🏢 Gestão Empresarial e Multi-Tenancy
- **Segregação de Dados**: Ambiente multi-empresa (SaaS) com isolamento total de dados por CNPJ.
- **Hierarquia Interna**: Gestão de departamentos, setores e cargos.
- **Gestão de Funcionários**: Cadastro individual ou importação em massa via **CSV**.
- **Dashboard de Engajamento**: Monitoramento em tempo real da taxa de participação e progresso das coletas.

### 🧠 Diagnóstico e Coleta Especializada
- **Instrumentos Validados**: Aplicação de 160 questões cobrindo:
    - **IMCO**: Clima e Cultura Organizacional.
    - **FDAC**: Dissonância entre cultura declarada e percebida.
    - **NRs (01, 17 e 12)**: Fatores de risco psicossocial, ergonômico e de segurança.
- **Sessões de Coleta**: Criação de links únicos para colaboradores com validade temporária.
- **Interface Mobile-First**: Experiência fluida para resposta em qualquer dispositivo.

### 📄 Motor de Laudos (TextEngine + IA)
- **TextEngine**: Motor determinístico que vincula cada resposta a uma base bibliográfica técnica (Goulart, 2025).
- **Inteligência Artificial**: Integração com **Groq (Llama-3.3)** para análise de sentimentos e recomendações automáticas para o PGR.
- **Cascata de Documentos**:
    - Laudo Individual (Devolutiva ao colaborador).
    - Anexo PCMSO (Pronto para medicina do trabalho).
    - Laudo Setorial/Departamental (Para gestores).
    - Relatório Pericial Organizacional (Para auditoria).

### 🔐 Segurança, Compliance e LGPD
- **Assinatura Eletrônica**: Sistema de selagem (sealing) de documentos com registro de hash.
- **Validação de Laudos**: Portal público para verificação de autenticidade via UUID/QR Code.
- **LGPD**: Fluxo obrigatório de consentimento de dados e transparência no tratamento de informações sensíveis.
- **Integração Gov.br**: Suporte técnico para assinaturas digitais certificadas.

---

## 🏛️ Arquitetura de Governança (Níveis de Acesso)

O sistema possui 6 níveis de permissão para garantir que a informação chegue apenas a quem tem direito legal:

1.  **Admin Master**: Controle global e faturamento do SaaS.
2.  **Company Admin**: Gestor de RH/SST da empresa cliente.
3.  **Manager**: Gestores de setor (acesso a dados agregados).
4.  **Manager Employee**: Gestor que também participa como respondente.
5.  **Employee**: Resposta e visualização da própria devolutiva.
6.  **Affiliate**: Consultores externos que gerenciam múltiplas empresas parceiras.

---

## 🛠️ Tecnologias e Stack

- **Backend**: Python 3.12 / Django 5.x
- **Frontend**: Vanilla JS + CSS Moderno (Design System customizado).
- **IA**: Groq API (Llama-3.3-70b).
- **Relatórios**: WeasyPrint + Jinja2 (PDFs periciais de alta fidelidade).
- **Pagamentos**: Stripe (Gestão de planos recorrentes).
- **Infraestrutura**: PostgreSQL + Railway (CI/CD Automático).

---

## 🚀 Como Executar Localmente

1. **Clone**: `git clone [url-do-repositorio]`
2. **Ambiente**: `python -m venv .venv` e `source .venv/bin/activate`
3. **Dependências**: `pip install -r requirements.txt`
4. **Variáveis**: Configure o arquivo `.env` baseado no `.env.example`
5. **Migrate**: `python manage.py migrate`
6. **Init**: `python manage.py setup_initial_data`
7. **Run**: `python manage.py runserver`

---

## 🛑 Regras de Negócio Críticas
- **R1 — Exclusividade Bibliográfica**: Todo item no laudo deve possuir rastreabilidade acadêmica.
- **R2 — Rastreabilidade por CPF**: Histórico do colaborador preservado conforme normas do MTE.
- **R3 — FDAC Goulart**: Conformidade estrita com o framework de governança 2025.
- **R4 — Saída PGR/GRO**: Foco em documentação defensível para o Ministério do Trabalho.

---
© 2026 SIMDCCONR01 — Tecnologia para Saúde Mental e Compliance.
