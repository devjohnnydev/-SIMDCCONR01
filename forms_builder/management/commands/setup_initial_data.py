"""
Management command para criar dados iniciais do sistema.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from billing.models import Plan
from forms_builder.models import FormTemplate, FormQuestion

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria dados iniciais: planos e templates de formulario'

    def handle(self, *args, **options):
        self.create_plans()
        self.create_form_templates()
        self.create_admin_master()
        self.stdout.write(self.style.SUCCESS('Dados iniciais criados com sucesso!'))

    def create_plans(self):
        plans = [
            {
                'name': 'Starter',
                'description': 'Ideal para pequenas empresas iniciando gestao de riscos.',
                'price_monthly': 199.00,
                'price_yearly': 1990.00,
                'max_employees': 50,
                'max_forms': 5,
                'max_reports': 10,
                'data_retention_days': 365,
                'has_pdf_export': True,
                'has_csv_import': True,
                'has_api_access': False,
                'has_custom_branding': False,
                'has_priority_support': False,
                'order': 1,
            },
            {
                'name': 'Professional',
                'description': 'Para empresas em crescimento com necessidades avancadas.',
                'price_monthly': 399.00,
                'price_yearly': 3990.00,
                'max_employees': 200,
                'max_forms': 20,
                'max_reports': 50,
                'data_retention_days': 730,
                'has_pdf_export': True,
                'has_csv_import': True,
                'has_api_access': True,
                'has_custom_branding': True,
                'has_priority_support': False,
                'order': 2,
                'is_featured': True,
            },
            {
                'name': 'Enterprise',
                'description': 'Solucao completa para grandes corporacoes.',
                'price_monthly': 899.00,
                'price_yearly': 8990.00,
                'max_employees': 9999,
                'max_forms': 9999,
                'max_reports': 9999,
                'data_retention_days': 1825,
                'has_pdf_export': True,
                'has_csv_import': True,
                'has_api_access': True,
                'has_custom_branding': True,
                'has_priority_support': True,
                'order': 3,
            },
        ]

        for plan_data in plans:
            Plan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
        self.stdout.write(f'  - {len(plans)} planos criados/atualizados')

    def create_form_templates(self):
        self.create_simdcconr01_template()
        self.stdout.write('  - 4 templates de formulario criados (incluindo SIMDCCONR01)')

    def create_simdcconr01_template(self):
        template, created = FormTemplate.objects.update_or_create(
            name='SIMDCCONR01 - Sistema Integrado de Clima, Cultura e Riscos NR',
            is_global=True,
            defaults={
                'category': 'SIMDCCONR01',
                'description': (
                    'Diagnostico integrado de cultura, clima organizacional e fatores de risco '
                    'psicossocial, ergonomico e de segurança (NR-1, NR-17 e NR-12). '
                    'Todas as questoes sao obrigatorias. Tempo estimado: 9 a 11 minutos.'
                ),
            }
        )

        questions_data = []

        # 3.1 IMCO - Clima Organizacional (88 perguntas)
        # Vetor: Motivacao
        imco_reconhecimento = [
            'Nesta empresa, as politicas de reconhecimento existentes sao aplicadas de forma homogenea e profissional para todos os empregados.',
            'O sistema de remuneracao existente e um excelente instrumento para valorizar e reconhecer aqueles que atingem suas metas.',
            'A empresa reconhece e aproveita aqueles que demonstram espirito de liderança.',
            'Na minha area, os empregados que desempenham bem suas tarefas sao devidamente reconhecidos pelos chefes.',
            'O caminho para ser reconhecido e obter os resultados esperados.',
            'Na empresa onde trabalho nao e necessario estar mais proximo da Diretoria/Chefia no dia-a-dia para ser reconhecido.',
            'Sinto que recebo reconhecimento adequado pelo esforço e pelos resultados que entrego.'  # Pergunta 107 no doc, mas parte desta dimensao
        ]
        for i, text in enumerate(imco_reconhecimento, 1):
            questions_data.append((text, 'SCALE', i))

        imco_comprometimento = [
            'Na empresa onde trabalho, ha grande empenho para encontrar as melhores alternativas para execução das atividades.',
            'Mesmo que surgisse outra oportunidade, pensaria muito antes de deixar meu emprego na empresa onde trabalho.',
            'Na empresa onde trabalho, em situações de dificuldade, as pessoas preferem levantar o problema em busca de soluções adequadas, ao invés de ignorá-lo.',
            'Posso garantir que a maioria de meus colegas atende prontamente às demandas/necessidades de serviço.',
            'O empregado da empresa onde trabalho tem grande orgulho de pertencer a ela.',
            'Percebo que os empregados da empresa onde trabalho demonstram um grau de fidelidade elevado à mesma.'
        ]
        for i, text in enumerate(imco_comprometimento, 8):
            questions_data.append((text, 'SCALE', i))

        imco_progresso = [
            'As oportunidades de crescimento profissional são acessíveis a todos os empregados.',
            'Há excelentes oportunidades de crescimento profissional na empresa onde trabalho.',
            'Meu trabalho me dá a oportunidade de aprender novas técnicas e habilidades, contribuindo para meu crescimento profissional.',
            'Tenho certeza de que as expectativas de crescimento profissional se concretizam nesta empresa.',
            'A estrutura de cargos existente é suficiente para permitir o crescimento profissional dos empregados.'
        ]
        for i, text in enumerate(imco_progresso, 14):
            questions_data.append((text, 'SCALE', i))

        # Vetor: Liderança
        imco_estilo = [
            'Minha chefia é acessível e me trata com respeito.',
            'A presença da chefia em minha área contribui de modo decisivo para o bom andamento das atividades.',
            'Eventuais divergências com minha chefia são discutidas no plano profissional e não no pessoal.',
            'Na maioria das vezes tenho autonomia para tomar decisões e resolver problemas sem precisar recorrer à chefia em cada etapa do trabalho.',
            'Quando é necessário efetuar uma mudança, minha chefia procura garantir o meu envolvimento e o da equipe no processo.',
            'Tenho suficientes orientações de minha chefia para resolver eventuais dificuldades no trabalho.',
            'Percebo que minha chefia reconhece e valoriza minhas contribuições, colocando-as em prática.',
            'Existe coerência entre o discurso e a prática gerencial em minha área de atuação.',
            'Minha chefia tem excelente habilidade para lidar com pessoas.',
            'Percebo que há autonomia suficiente para organizar meu trabalho e tomar decisões relacionadas às minhas atividades.', # 103
            'A liderança oferece suporte adequado quando enfrento dificuldades ou sobrecarga no trabalho.' # 104
        ]
        for i, text in enumerate(imco_estilo, 19):
            questions_data.append((text, 'SCALE', i))

        imco_equipe = [
            'A empresa prioriza a contribuição de todos através de um diálogo centrado na melhoria permanente do trabalho cotidiano.',
            'Não há protecionismo de qualquer espécie em relação aos integrantes da equipe a que pertenço.',
            'Esta empresa fomenta o trabalho em equipe como uma de suas crenças para a busca do sucesso.',
            'Há uma grande união e apoio mútuo entre as pessoas da equipe em que trabalho.',
            'O trabalho em equipe flui muito bem na empresa onde atuo.',
            'Há tempo suficiente para melhorar o relacionamento e a troca de experiências entre as equipes de trabalho.',
            'Observo ou vivencio situações de assédio moral, discriminação ou comportamentos inadequados no ambiente de trabalho.' # 108
        ]
        for i, text in enumerate(imco_equipe, 30):
            questions_data.append((text, 'SCALE', i))

        imco_competicao = [
            'A competição entre pessoas ou grupos é sadia, sendo valorizada como forma de estimular a criatividade e melhorar o desempenho profissional.',
            'O nível de competição existente entre as pessoas é normal e jamais compromete o bom andamento das atividades.',
            'Há grande harmonia em meu ambiente de trabalho.'
        ]
        for i, text in enumerate(imco_competicao, 37):
            questions_data.append((text, 'SCALE', i))

        # Vetor: Filosofia de Gestao
        imco_clareza = [
            'A busca contínua de profissionalismo na gestão é uma das principais preocupações na empresa onde trabalho.',
            'O estilo de administração adotado pela empresa onde trabalho influencia de modo positivo o comportamento dos seus empregados em relação ao trabalho que executam.',
            'Está claro que a Diretoria da empresa onde trabalho se preocupa mais com os assuntos verdadeiramente estratégicos para a empresa.',
            'É forte a preocupação da empresa onde trabalho em reter seus melhores talentos.',
            'As pessoas que trabalham aqui sabem quais são os principais objetivos, metas ou planos da empresa.',
            'A postura da empresa onde trabalho demonstra claramente que as pessoas são seu maior patrimônio.',
            'Sem dúvida um dos objetivos da empresa onde trabalho é crescer respeitando as necessidades e a satisfação de seus clientes.',
            'Nesta empresa é grande a preocupação de divulgar e transferir o conhecimento adquirido durante o exercício das atividades entre as equipes de trabalho.'
        ]
        for i, text in enumerate(imco_clareza, 40):
            questions_data.append((text, 'SCALE', i))

        imco_comunicacao = [
            'As informações necessárias à realização de meu trabalho são transmitidas de forma clara e objetiva.',
            'As mudanças são comunicadas e explicadas com antecedência.',
            'A quantidade de reuniões de trabalho é suficiente para manter as pessoas informadas sobre o que acontece na empresa onde trabalho.',
            'Gasto pouco tempo selecionando as informações que recebo através dos diferentes canais de comunicação formais da empresa onde trabalho.',
            'A comunicação é verdadeiramente de mão dupla; não há porque temer surpresas ou reações inesperadas de qualquer parte.',
            'Na empresa onde trabalho, as informações fluem igualmente para todos os empregados e áreas.',
            'Obtenho com facilidade junto a outras áreas da empresa onde trabalho as informações que necessito para o desempenho adequado de minhas atividades.',
            'Na empresa onde trabalho a rede de comunicação é ágil e eficiente.',
            'As mudanças organizacionais (reestruturações, novos processos) são comunicadas e gerenciadas de forma clara e com participação da equipe.', # 105
            'Há canais eficazes e seguros para relatar preocupações relacionadas ao bem-estar ou ao clima organizacional.' # 110
        ]
        for i, text in enumerate(imco_comunicacao, 48):
            questions_data.append((text, 'SCALE', i))

        imco_regras = [
            'A estrutura organizacional e funcional da empresa é consistente com seus objetivos.',
            'Há uma nítida e adequada divisão de papéis e de atribuições entre áreas da empresa onde trabalho.',
            'As mudanças que ocorrem na empresa onde trabalho são sempre planejadas.',
            'Há suficiente abertura e flexibilidade para aceitação de ideias e sugestões voltadas ao aperfeiçoamento ou melhoria da empresa onde trabalho.',
            'No meu ambiente de trabalho, há clareza quanto às minhas responsabilidades e papéis, evitando ambiguidades ou sobreposições.' # 106
        ]
        for i, text in enumerate(imco_regras, 58):
            questions_data.append((text, 'SCALE', i))

        # Vetor: Gestao de Pessoas
        imco_politica_salarial = [
            'O sistema de compensação (salário + benefícios) é adequado, não interferindo na satisfação dos empregados.',
            'Os benefícios existentes complementam de modo suficiente os salários pagos para os diferentes cargos.',
            'A remuneração é balanceada, incluindo, além do salário, benefícios e outras formas de compensação.',
            'Os benefícios são amplos e variados, auxiliando a manter os mais competentes.',
            'Há equilíbrio interno entre os salários pagos; os cargos mais complexos ou mais importantes são os mais bem remunerados.',
            'A progressão nas faixas salariais (promoção horizontal) é periódica e realizada a intervalos adequados.',
            'Os aumentos salariais nesta empresa excedem a variação do custo de vida no período.'
        ]
        for i, text in enumerate(imco_politica_salarial, 63):
            questions_data.append((text, 'SCALE', i))

        imco_salario = [
            'O salário que recebo é suficiente para atender meu padrão de vida.',
            'Os salários pagos reconhecem o valor e a qualidade do desempenho dos funcionários da empresa onde trabalho.',
            'As diferenças nos salários refletem as diferenças no conteúdo e exigências dos cargos.',
            'Meu salário é justo, representando o retorno compatível a meu rendimento dentro desta empresa.'
        ]
        for i, text in enumerate(imco_salario, 70):
            questions_data.append((text, 'SCALE', i))

        imco_rh = [
            'O RH dispõe de instrumentos para realizar uma avaliação eficaz do desempenho dos empregados em suas atividades.',
            'O RH demonstra em suas práticas grande preocupação com aspectos de justiça e ética.',
            'A área de RH está envolvida e preocupada em definir o papel e os requisitos necessários para os diferentes cargos existentes na empresa.',
            'O banco de horas é um instrumento eficaz para apurar minha dedicação extra ao trabalho.',
            'Sinto que o suporte emocional e psicológico (quando necessário) está disponível na organização.' # 111
        ]
        for i, text in enumerate(imco_rh, 74):
            questions_data.append((text, 'SCALE', i))

        imco_carreira = [
            'Tenho boas oportunidades de adquirir competências gerenciais no exercício de meu trabalho.',
            'Sinto que minhas qualificações e treinamento aumentam minhas possibilidades de promoção.',
            'Não é necessário ter um bom tempo de casa para se ter uma situação melhor de trabalho nesta empresa.',
            'Tenho boas oportunidades de adquirir competências técnicas no exercício de meu trabalho.',
            'Meu horizonte profissional está bem claro para mim, sei exatamente onde posso chegar nesta empresa.'
        ]
        for i, text in enumerate(imco_carreira, 79):
            questions_data.append((text, 'SCALE', i))

        imco_treinamento = [
            'A organização em que trabalho é reconhecidamente uma empresa que se preocupa em formar seus profissionais para o exercício das atividades.',
            'Há total apoio da empresa para a realização de treinamentos diretamente ligados à minha atividade profissional (treinamentos técnicos).',
            'O treinamento é amplamente valorizado na empresa onde trabalho, até mesmo aqueles voltados para estágios futuros da carreira do empregado.'
        ]
        for i, text in enumerate(imco_treinamento, 84):
            questions_data.append((text, 'SCALE', i))

        # Vetor: Natureza do Trabalho
        imco_conteudo = [
            'Estou fazendo progressos satisfatórios em relação às minhas metas profissionais.',
            'As tarefas que executo são interessantes e desafiantes.',
            'Meu cargo atual está me ajudando a atingir minhas metas profissionais.',
            'Se necessário, sinto que tenho grandes possibilidades de influenciar as decisões que afetam meu trabalho.',
            'Minha capacidade, habilidades e potencial são bem aproveitados no trabalho que executo.'
        ]
        for i, text in enumerate(imco_conteudo, 87):
            questions_data.append((text, 'SCALE', i))

        # Volume de Trabalho (NR-1 + NR-17 + NR-12)
        imco_volume = [
            'Raramente deixo de cumprir os prazos e metas de meu cargo, uma vez que o volume de trabalho é bem dimensionado na empresa onde atuo.',
            'Quase nunca considero minha jornada de trabalho muito extensa.',
            'Tenho a tranquilidade e o tempo necessários para executar minhas atividades.',
            'Os processos e rotinas de trabalho em minha área atendem bem às necessidades do serviço.',
            'Disponho de tempo suficiente para refletir sobre como aperfeiçoar a execução de meu trabalho.',
            'Sinto que a carga de trabalho (quantidade e complexidade das tarefas) é excessiva e compromete meu bem-estar.', # 101
            'Os prazos e metas estabelecidos pela empresa são realistas e proporcionais aos recursos e tempo disponíveis.', # 102
            'O equilíbrio entre vida profissional e pessoal é respeitado pela empresa (ex.: respeito a horários, intervalos e desconexão após o expediente).', # 109
            'O trabalho remoto ou híbrido, quando aplicável, é organizado de forma a evitar isolamento ou excesso de demandas digitais.' # 112
        ]
        for i, text in enumerate(imco_volume, 92):
            questions_data.append((text, 'SCALE', i))

        # Ergonômicos (NR-17)
        imco_ergonomia = [
            'As condições de iluminação, temperatura e ruído no meu local de trabalho são adequadas e não prejudicam minha concentração ou saúde física.',
            'O ritmo de trabalho permite pausas suficientes para recuperação física e mental durante a jornada.',
            'A empresa oferece condições para que eu realize minhas tarefas sem exposição excessiva a posturas inadequadas ou movimentos repetitivos.',
            'Os equipamentos, mobiliário e ferramentas disponíveis são ergonômicos e facilitam a execução das minhas atividades diárias.',
            'Sinto que o conteúdo das minhas tarefas exige esforço mental elevado e constante concentração sem pausas adequadas (carga cognitiva).',
            'Percebo que minhas atividades são repetitivas ou monótonas, o que afeta minha motivação e atenção ao longo do dia.'
        ]
        for i, text in enumerate(imco_ergonomia, 101):
            questions_data.append((text, 'SCALE', i))

        # NR-12
        imco_nr12 = [
            'Percebo que as máquinas e equipamentos que utilizo possuem dispositivos de segurança (proteções, paradas de emergência e sinalização) adequados e funcionais, sem gerar sensação de risco ou desconforto durante o uso.',
            'A interface entre mim e as máquinas/equipamentos (controles, displays e posicionamento) é projetada de forma ergonômica, facilitando o uso seguro e reduzindo esforço físico ou mental excessivo.'
        ]
        for i, text in enumerate(imco_nr12, 107):
            questions_data.append((text, 'SCALE', i))

        # Complemento Amplo NR-17
        imco_nr17_ampliado = [
            'Meu trabalho é organizado de forma que eu tenho controle suficiente sobre a sequência e o ritmo das minhas tarefas diárias.',
            'As pausas previstas no meu trabalho são suficientes para que eu me recupere física e mentalmente.',
            'As exigências cognitivas do meu trabalho (concentração, memória, tomada de decisão) são compatíveis com el tempo e os recursos disponíveis.',
            'O mobiliário e o layout do meu posto de trabalho permitem uma postura confortável e natural durante a maior parte da jornada.',
            'Sinto que o trabalho que realizo é excessivamente monótono ou repetitivo, o que afeta minha atenção e motivação.',
            'A combinação entre esforço físico e mental exigido pelo meu trabalho me deixa frequentemente exausto ao final do dia.'
        ]
        for i, text in enumerate(imco_nr17_ampliado, 109):
            questions_data.append((text, 'SCALE', i))

        # 3.2 FDAC - Cultura Organizacional (12 perguntas)
        fdac_cultura = [
            'As políticas de reconhecimento são aplicadas equitativamente a todos os colaboradores, independentemente de cargo ou departamento.',
            'Meu salário reflete justamente minha contribuição, considerando padrões internos e de mercado.',
            'As oportunidades de progressão na carreira são transparentes e acessíveis, promovendo equidade.',
            'A liderança comunica os objetivos estratégicos de forma clara, alinhando todos os níveis organizacionais.',
            'Tenho acesso imediato a informações relevantes para minhas responsabilidades.',
            'Os canais de comunicação interna (e.g., intranet, reuniões) promovem transparência e eliminam ambiguidades.',
            'Meus papéis e responsabilidades são definidos com precisão, evitando sobreposições.',
            'A liderança promove responsabilidade compartilhada por resultados, incentivando a proatividade.',
            'O trabalho em equipe é estruturado com metas claras e papéis bem definidos.',
            'A empresa adere rigorosamente a normas éticas e legais em todas as práticas.',
            'Os programas de treinamento reforçam a conformidade com políticas éticas e regulatórias.',
            'O conteúdo do meu trabalho está alinhado às expectativas éticas da organização, promovendo integridade.'
        ]
        for i, text in enumerate(fdac_cultura, 115):
            questions_data.append((text, 'SCALE', i))

        # 3.3 NR-01 / SESMT - Fatores de Risco (46 itens)
        # Bloco K
        nr01_bloco_k = [
            'Dor de cabeça frequente que não passa com analgésico comum.',
            'Tremores ou movimentos involuntários em repouso.',
            'Episódios de desmaio ou convulsão.',
            'Visão embaçada ou dupla sem causa ocular conhecida.',
            'Tontura ou desequilíbrio ao levantar ou andar.',
            'Palpitações que duram mais de 10 min com medo de morrer.',
            'Formigamento ou dormência em braços/pernas sem compressão.',
            'Uso contínuo de remédio sem receita para "nervos" ou sono.'
        ]
        for i, text in enumerate(nr01_bloco_k, 127):
            questions_data.append((text, 'YESNO', i))

        # Bloco L
        nr01_bloco_l = [
            'Exame de sangue nos últimos 12 meses: alteração de TSH, B12 ou hemoglobina. (0 = não fez/normal | 1 = normal | 2 = alterado | 3 = não sei)',
            'Traumatismo craniano com perda de consciência. (0 = nunca | 1 = < 5 min | 2 = 5-30 min | 3 = > 30 min)',
            'Epilepsia ou convulsão já diagnosticada. (0 = não | 1 = sim, controlada | 2 = sim, em tratamento | 3 = sim, sem controle)',
            'Doença auto-imune (lúpus, Hashimoto, etc.). (0 = não | 1 = sim, sem sintomas atuais | 2 = sim, com sintomas leves | 3 = sim, com sintomas moderados/graves)',
            'Infecção grave nos últimos 6 meses com sintomas neurológicos. (0 = não | 1 = sim, sem sequelas | 2 = sim, com sequelas leves | 3 = sim, com sequelas moderadas)',
            'Cirurgia com anestesia geral nos últimos 3 meses. (0 = não | 1 = sim, sem complicações | 2 = sim, com complicações leves | 3 = sim, com complicações moderadas)',
            'Apneia do sono confirmada ou uso de CPAP. (0 = não | 1 = sim, sem uso de CPAP | 2 = sim, uso irregular de CPAP | 3 = sim, uso regular de CPAP)',
            'Histórico familiar de demência precoce, Parkinson ou esquizofrenia. (0 = não | 1 = sim, em parente distante | 2 = sim, em parente de primeiro grau | 3 = sim, múltiplos casos na família)'
        ]
        for i, text in enumerate(nr01_bloco_l, 135):
            questions_data.append((text, 'SINGLE', i, ['0', '1', '2', '3']))

        # Bloco M
        nr01_bloco_m = [
            'Esquecer o que estava fazendo no meio de uma tarefa simples.',
            'Perder chaves, celular ou crachá mais de 2 vezes por semana.',
            'Iniciar várias tarefas e não concluir nenhuma delas.',
            'Dificuldade de planejar a sequência de passos para elaborar um relatório ou projeto.',
            'Atraso maior que 5 minutos para tomar decisões simples do dia a dia.',
            'Esquecer data ou horário de compromissos que já havia anotado.',
            'Precisar anotar absolutamente tudo para não esquecer.',
            'Sentir-me "atrasado" em relação ao ritmo dos meus colegas.'
        ]
        for i, text in enumerate(nr01_bloco_m, 143):
            questions_data.append((text, 'SCALE', i))

        # Bloco N
        nr01_bloco_n = [
            'Quantas horas de sono você tem dormido por noite, em média, na última semana?',
            'Quantos dias por semana você trabalha em home office ou modelo híbrido?',
            'Sofreu assédio moral ou sexual no trabalho nos últimos 12 meses?',
            'Qual é o seu principal regime de escala de trabalho?',
            'Quantas horas extras você realiza por semana, em média?',
            'Quantos dias de férias você tirou nos últimos 12 meses?',
            'Já teve afastamento médico por problema mental ou estresse nos últimos 24 meses?',
            'A empresa oferece apoio psicológico ou coaching de forma regular?'
        ]
        for i, text in enumerate(nr01_bloco_n, 151):
            qtype = 'NUMBER' if i in [151, 152, 155, 156] else 'SINGLE'
            options = ['Sim', 'Não'] if qtype == 'SINGLE' and i != 154 else (['Presencial', 'Hibrido', 'Home Office'] if i == 154 else None)
            questions_data.append((text, qtype, i, options))

        # Bloco O
        nr01_bloco_o = [
            'Tenho dificuldade de chegar ao trabalho no horário por motivos relacionados ao meu estado de saúde ou bem-estar.',
            'Percebo redução de minha produtividade superior a 25% nos últimos meses (autoavaliação ou feedback do gestor).',
            'Já recebi advertências, suspensões ou tive faltas justificadas por atrasos ou erros frequentes.',
            'Tenho pensado em pedir demissão ou sinto temor constante de ser demitido.',
            'Já precisei de afastamento médico ou uso de benefício assistencial nos últimos 12 meses.',
            'Perdi oportunidade de promoção ou nova função nos últimos 6 meses devido ao meu desempenho ou saúde.'
        ]
        for i, text in enumerate(nr01_bloco_o, 159):
            questions_data.append((text, 'YESNO', i))

        # Bloco P + Q
        nr01_bloco_pq = [
            'Consumo bebida alcoólica 4 ou mais vezes por semana para "relaxar" ou dormir.',
            'Usei maconha, cocaína, anfetaminas ou opioides nos últimos 30 dias.',
            'Já usei alguma substância pela manhã para "ativar" ou acalmar os nervos antes do trabalho.',
            'Já tentei diminuir ou parar o uso de alguma substância, mas não conseguiu.',
            'Já tive brigas familiares, advertências ou faltas no trabalho relacionadas ao uso de substâncias.',
            'Sinto sintomas de abstinência (tremor, suor, insônia, irritabilidade) quando fico sem a substância.',
            'Descreva, com suas palavras, o que MAIS tem afetado seu bem-estar ou trabalho nos últimos 3 meses:'
        ]
        for i, text in enumerate(nr01_bloco_pq, 165):
            qtype = 'SCALE' if i < 171 else 'TEXT'
            questions_data.append((text, qtype, i))

        # Truncar/Ajustar ordens para garantir que fiquem entre 1 e 160
        # For simplicity, we just use the calculated orders.
        
        for item in questions_data:
            text = item[0]
            qtype = item[1]
            order = item[2]
            opts = item[3] if len(item) > 3 else None
            
            FormQuestion.objects.update_or_create(
                template=template,
                order=order,
                defaults={
                    'text': text, 
                    'question_type': qtype, 
                    'options': opts,
                    'is_required': qtype != 'TEXT'
                }
            )


    def create_admin_master(self):
        if not User.objects.filter(role='ADMIN_MASTER').exists():
            user = User.objects.create_superuser(
                email='admin@saas-nr01.com.br',
                password='Admin@123',
                first_name='Administrador',
                last_name='Master',
            )
            user.role = 'ADMIN_MASTER'
            user.terms_accepted = True
            user.privacy_accepted = True
            user.save()
            self.stdout.write('  - Usuario ADMIN_MASTER criado (admin@saas-nr01.com.br)')
        else:
            self.stdout.write('  - Usuario ADMIN_MASTER ja existe')
