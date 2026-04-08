# SIMDCCONR01 — Sistema de Compliance NR-01, NR-17 e NR-12

![SIMDCCONR01 Banner](https://img.shields.io/badge/Status-Project_Completed-success?style=for-the-badge&logo=django)
![Compliance](https://img.shields.io/badge/Compliance-NR--01%20|%20NR--17%20|%20NR--12-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)

O **SIMDCCONR01** é uma plataforma SaaS (Software as a Service) de alta performance projetada para a gestão de conformidade em Saúde e Segurança do Trabalho (SST). O sistema integra medições psicossociais, neurocognitivas e ergonômicas, gerando laudos periciais determinísticos e auditáveis para atender às exigências das Normas Regulamentadoras brasileiras.

---

## 🏛️ Arquitetura de Governança (Níveis de Acesso)

O sistema possui uma hierarquia rigorosa de permissões segregadas em 6 níveis funcionais:

1.  **Admin Master (SaaS Owner)**: Controle total da plataforma, gestão de planos e aprovação de novas empresas.
2.  **Company Admin**: Gestor principal da empresa cliente. Controla setores, funcionários e orquestra as avaliações.
3.  **Manager (Gestor de Setor)**: Acesso aos laudos consolidados (departamentais) de sua área de atuação.
4.  **Manager Employee**: Versão híbrida para gestores que também devem responder às avaliações.
5.  **Employee (Colaborador)**: Acesso exclusivo para resposta de questionários e visualização de sua própria devolutiva.
6.  **Affiliate (Afiliado/Consultor)**: Perfil para profissionais que trazem novas empresas e acompanham a implantação.

---

## 🧠 Motor de Texto Determinístico (TextEngine)

Diferente de sistemas baseados em IA generativa (que podem "alucinar" dados), o SIMDCCONR01 utiliza o **TextEngine**, um motor de regras periciais fixas:

- **Rastreabilidade Total**: Cada item do laudo individual (1 a 160) está vinculado a um constructo e uma base bibliográfica.
- **Fundamentação Técnica**: O sistema utiliza o framework **FDAC**, fundamentado na obra de **Goulart (2025)**.
- **Zero Aleatoriedade**: Resultados 100% reproduzíveis e defensíveis em auditorias fiscais ou processos trabalhistas.

---

## 📋 Módulos de Diagnóstico (Instrumentos)

A plataforma processa mais de 160 variáveis organizadas nos seguintes blocos:

- **IMCO (88 itens)**: Índice de Medida de Clima e Cultura Organizacional (Litwin & Stringer, Coda).
- **FDAC (12 itens)**: Fairness, Disclosure, Accountability & Compliance (Goulart).
- **Blocos NR**:
    - **NR-01 (GRO/PGR)**: Fatores orgânicos e organizacionais de risco.
    - **NR-17 (Ergonomia)**: Sobrecarga cognitiva e psicossocial.
    - **NR-12 (Segurança)**: Percepção de risco em máquinas e equipamentos.

---

## 📄 Hierarquia de Saída (Relatórios)

O sistema gera uma cascata de documentos técnicos essenciais:

1.  **Laudo Individual (Respondente)**: Devolutiva para o colaborador com rastreabilidade item a item.
2.  **Anexo PCMSO (Saúde Ocupacional)**: Documento médico padronizado para integração imediata ao prontuário clínico.
3.  **Laudo de Departamento (Setorial)**: Consolidação estatística para gestores identificarem focos de estresse ou risco.
4.  **Laudo Pericial Organizacional**: Documento mestre de compliance para a empresa, integrável ao **PGR/GRO**.

---

## 🔐 Compliance e Assinatura Eletrônica

Para garantir validade jurídica (R1 a R5 das regras de negócio), o sistema oferece:

- **Assinatura Interna**: Com carimbo de tempo e hash de validação.
- **Integração Gov.br**: Suporte a assinaturas digitais certificadas pelo governo federal brasileiro.
- **Perfil de Signatário**: Gestão de registros profissionais (CRP, CRM, CREA) de psicólogos, médicos e engenheiros.

---

## 🛠️ Tecnologias e Stack

- **Backend**: Django 5.x / Python 3.11+
- **Frontend**: Vanilla JS + CSS Premium (Glassmorphism & Design System personalizado).
- **PDF Engine**: WeasyPrint (Geração de documentos periciais com alta fidelidade visual).
- **Payments**: Stripe (Gestão de assinaturas e planos recorrentes).
- **Database**: PostgreSQL (Pronto para alta escala e concorrência).

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.11+
- Ferramenta de build/packages (Pip ou UV)

### Passo a Passo
1. Clone o repositório.
2. Crie e ative o ambiente virtual.
3. Instale as dependências: `pip install -r requirements.txt`.
4. Configure as variáveis de ambiente no arquivo `.env` (use `.env.example` como base).
5. Execute as migrações: `python manage.py migrate`.
6. Carregue os dados iniciais: `python manage.py setup_initial_data`.
7. Opcional: Gere protótipos de teste: `python manage.py generate_prototype_data`.
8. Inicie o servidor: `python manage.py runserver`.

---

## 🛑 Regras de Negócio Críticas (Resumo)
- **🔴 R1 — Exclusividade Bibliográfica**: Sem fundamentação, sem laudo.
- **🔴 R2 — Rastreabilidade Total**: 160/160 itens devem ter origem comprovada.
- **🔴 R3 — FDAC Goulart (2025)**: Padrão ouro de compliance.
- **🔴 R4 — Saída PGR/GRO + PCMSO**: Foco em obrigatoriedade legal.
- **🔴 R5 — Hierarquia Formal**: Segregação de dados conforme nível de acesso.

---
© 2026 SIMDCCONR01 — Todos os direitos reservados.
