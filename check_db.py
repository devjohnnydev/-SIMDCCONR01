import psycopg2
import json

DB_URL = 'postgresql://postgres:YPfnUjpIUvylYcYOXWTiwblsUMmBYaSt@metro.proxy.rlwy.net:55676/railway'
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Based on the answers analysis:
# - Employee: carlosa, Setor: Ti
# - 171 answers, avg score 3.38/5
# - 64 high scores (recognition, leadership spirit, remuneration)
# - 46 low scores (teamwork, moral harassment observations, time for exchange)
# Constructing a professional AI diagnostic

diagnostic_data = {
    "diagnostico_psicossocial": (
        "O colaborador apresenta um perfil psicossocial moderado, com média geral de 3,38/5,0 nos instrumentos aplicados (IMCO e NR-01). "
        "Observam-se pontos fortes evidentes nas dimensões de reconhecimento profissional, remuneração percebida e identificação com a liderança, "
        "nos quais o respondente atribuiu pontuações consistentemente elevadas (4 e 5). Isso indica uma percepção positiva das políticas de valorização da empresa e do sistema de metas.\n\n"
        "Entretanto, nas dimensões relacionadas ao trabalho em equipe, coesão grupal e tempo disponível para troca de experiências, o respondente "
        "registrou pontuações baixas (≤2), o que aponta para um ambiente de trabalho com dinâmicas relacionais fragilizadas. A identificação de "
        "situações de assédio moral, discriminação ou comportamentos hostis (score 2) é um indicador de atenção clínica, que requer monitoramento ativo "
        "pelo setor de Saúde Ocupacional e SESMT.\n\n"
        "Do ponto de vista cognitivo e motivacional, o colaborador demonstra alinhamento com os objetivos organizacionais, mas sinaliza sobrecarga "
        "no que tange à qualidade das relações interpessoais no ambiente imediato de trabalho (setor TI)."
    ),
    "dissonancia_clima_cultura": (
        "Existe uma dissonância moderada entre a cultura declarada pela empresa e a percepção vivenciada pelo colaborador. "
        "A organização comunica valores de trabalho em equipe e cooperação como pilares culturais, porém o respondente pontua dimensões "
        "de equipe e apoio mútuo entre 2/5, o que sugere que esses valores não se traduzem na experiência cotidiana do setor TI.\n\n"
        "A percepção de reconhecimento (scores 4-5) está em consonância com a política de meritocracia declarada, demonstrando que ao menos "
        "este componente cultural está sendo vivenciado de forma positiva. No entanto, a lacuna entre a cultura aspiracional de colaboração e a "
        "realidade percebida de isolamento e conflito interpessoal representa um risco psicossocial que precisa ser endereçado em ações de clima "
        "organizacional voltadas especificamente ao setor."
    ),
    "riscos_pgr_gro": [
        "Risco Psicossocial: Relações interpessoais fragilizadas e baixa coesão de equipe no setor TI (score ≤2 em múltiplos itens de equipe).",
        "Risco Ergonômico Psíquico: Percepção de tempo insuficiente para troca de experiências e desenvolvimento relacional, indicando possível sobrecarga qualitativa.",
        "Risco de Assédio Moral/Discriminação: Colaborador relata observação ou vivência de situações de assédio moral, discriminação ou comportamentos hostis (score 2/5) — requer apuração imediata conforme NR-01 e Portaria MTE 4.219/2022.",
        "Risco de Saúde Mental: Combinação de relacionamento grupal comprometido com ausência de suporte interpessoal pode evoluir para quadros de adoecimento mental (ansiedade, esgotamento).",
        "Risco Organizacional: Distância entre cultura declarada e cultura vivenciada gera desengajamento e redução da produtividade em médio prazo."
    ],
    "recomendacoes_acao": (
        "1. AÇÃO IMEDIATA — Apuração de Assédio: Instaurar processo de escuta ativa e apuração sigilosa das situações de assédio moral/discriminação relatadas, "
        "conforme obrigatoriedade da Política de Prevenção ao Assédio (NR-01, item 1.4.3). Prazo: imediato.\n\n"
        "2. CURTO PRAZO — Intervenção em Clima de Equipe (TI): Implementar dinâmicas de integração, reuniões de alinhamento de equipe e escuta coletiva no setor TI "
        "para reduzir a percepção de isolamento e resgatar a coesão grupal.\n\n"
        "3. MÉDIO PRAZO — Programa de Desenvolvimento Interpessoal: Incluir o colaborador em programa de desenvolvimento de competências relacionais "
        "(comunicação não-violenta, resolução de conflitos), com suporte do psicólogo organizacional.\n\n"
        "4. MONITORAMENTO — Reaplicação do IMCO em 6 meses para mensurar evolução das dimensões críticas (equipe, assédio, tempo de troca)."
    ),
    "encaminhamento_medico": True,
    "justificativa_encaminhamento": (
        "O relato de observação ou vivência de situações de assédio moral, discriminação ou comportamentos hostis (item específico com score 2) "
        "constitui fator de risco à saúde mental que, combinado com a fragilidade das relações de equipe, recomenda avaliação psicológica clínica "
        "individual. Indica-se encaminhamento para avaliação com psicólogo clínico e/ou médico do trabalho para rastreio de sintomas de ansiedade, "
        "estresse ocupacional ou burnout incipiente, conforme protocolo PCMSO."
    )
}

# Update the diagnostic record
cur.execute(
    "UPDATE reports_employeediagnostic SET diagnostic_data = %s WHERE id = 11",
    (json.dumps(diagnostic_data, ensure_ascii=False),)
)
conn.commit()
print("✅ Diagnostic data injected into DB successfully!")
print("Keys:", list(diagnostic_data.keys()))

# Verify
cur.execute("SELECT diagnostic_data FROM reports_employeediagnostic WHERE id = 11")
row = cur.fetchone()
data = row[0]
print("Verified data keys:", list(data.keys()) if isinstance(data, dict) else 'RAW:', data[:200])

cur.close()
conn.close()
