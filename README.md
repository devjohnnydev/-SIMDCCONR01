# SIMDCCONR01 - Sistema de Compliance NR-01, NR-17 e NR-12

Sistema Informatizado de Medida de Dissonância de Cultura e Clima Organizacional integrado com as normas regulamentadoras NR-01 (GRO/PGR), NR-17 (Ergonomia) e NR-12 (Segurança em Máquinas).

## 🚀 Tecnologias
- **Backend:** Python 3.11+ / Django 5.x
- **Banco de Dados:** PostgreSQL (Produção) / SQLite (Desenvolvimento)
- **Motor de IA:** Groq (Llama-3.3-70b-versatile) para diagnósticos psicossociais.
- **Relatórios:** WeasyPrint (Geração de Laudos Periciais em PDF).
- **Hospedagem:** Railway (Preparado para Deploy contínuo).

## 📋 Funcionalidades Principais
- **Módulos de Diagnóstico:**
    - **IMCO (88 questões):** Medida de Clima Organizacional.
    - **FDAC (12 questões):** Modelo de Cultura Organizacional.
    - **Blocos NR-01/17/12 (60 questões):** Fatores de risco psicossocial, neurocognitivo e ergonômico.
- **Inteligência Artificial:** Análise automatizada de respostas para geração de laudos de PGR/GRO e sinalização de riscos.
- **Rastreabilidade Global:** Histórico vinculado ao CPF, permitindo herança de dados entre diferentes empresas (CNPJs).
- **Compliance LGPD:** Consentimento duplo (individual e agregado anônomo).
- **Automação:** Reaplicação semestral automática dos questionários.

## 🛠 Como Rodar (Desenvolvimento)

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt # ou use o uv
   ```

2. **Configuração de Ambiente (.env):**
   Crie um arquivo `.env` na raiz com:
   ```env
   GROQ_API_KEY=gsk_96hm...
   DATABASE_URL=postgres://user:pass@localhost:5432/db
   DEBUG=True
   ```

3. **Carga Inicial e Dados de Teste:**
   ```bash
   python manage.py migrate
   python manage.py setup_initial_data
   python manage.py generate_prototype_data
   ```

4. **Inicie o servidor:**
   ```bash
   python manage.py runserver
   ```

## 🚢 Deploy no Railway
O projeto já inclui `Procfile` e `railway.json`. 
- O comando de `release` rodará automaticamente as migrações e a carga de dados inicial.
- Configure a variável `GROQ_API_KEY` no painel do Railway.

## 📜 Licença
Propriedade intelectual conforme especificações técnicas do projeto SIMDCCONR01.
