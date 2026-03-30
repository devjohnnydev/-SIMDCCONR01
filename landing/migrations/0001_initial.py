from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LandingConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary_color', models.CharField(default='#2563EB', max_length=7, verbose_name='Cor Primária')),
                ('secondary_color', models.CharField(default='#0D9488', max_length=7, verbose_name='Cor Secundária')),
                ('accent_color', models.CharField(default='#7C3AED', max_length=7, verbose_name='Cor Destaque')),
                ('dark_bg_color', models.CharField(default='#0A0F1E', max_length=7, verbose_name='Fundo Escuro')),
                ('hero_badge', models.CharField(default='Nova Obrigação Legal — NR-1 / Portaria MTE 1.419/2024', max_length=200, verbose_name='Badge do Hero')),
                ('hero_title1', models.CharField(default='Saúde Mental no Trabalho', max_length=200, verbose_name='Título Linha 1')),
                ('hero_title2', models.CharField(default='não é opcional.', max_length=200, verbose_name='Título Linha 2')),
                ('hero_highlight', models.CharField(default='É lei. É urgente.', max_length=200, verbose_name='Título Destaque')),
                ('hero_subtitle', models.TextField(default='O sistema mais completo do Brasil para diagnóstico de riscos psicossociais, compliance NR-1, NR-17 e NR-12.', verbose_name='Subtítulo do Hero')),
                ('hero_cta_text', models.CharField(default='Proteja sua Empresa Agora', max_length=100, verbose_name='Texto CTA Hero')),
                ('hero_image', models.ImageField(blank=True, null=True, upload_to='landing/', verbose_name='Imagem de Fundo')),
                ('starter_price', models.DecimalField(decimal_places=2, default=297, max_digits=8, verbose_name='Preço Starter')),
                ('starter_employees', models.IntegerField(default=50, verbose_name='Max Func. Starter')),
                ('starter_description', models.CharField(default='Para PMEs até 50 colaboradores', max_length=200, verbose_name='Descrição Starter')),
                ('pro_price', models.DecimalField(decimal_places=2, default=697, max_digits=8, verbose_name='Preço Professional')),
                ('pro_employees', models.IntegerField(default=300, verbose_name='Max Func. Professional')),
                ('pro_description', models.CharField(default='Para empresas de 50 a 300 colaboradores', max_length=200, verbose_name='Descrição Professional')),
                ('enterprise_description', models.CharField(default='Para grupos e conglomerados +300', max_length=200, verbose_name='Descrição Enterprise')),
                ('enterprise_contact', models.EmailField(default='contato@simdcconr01.com.br', verbose_name='Email Enterprise')),
                ('cta_title', models.CharField(default='Sua empresa está pronta para a nova NR-1?', max_length=200, verbose_name='Título CTA Final')),
                ('cta_subtitle', models.TextField(default='Evite multas, proteja sua equipe e mantenha o PGR atualizado.', verbose_name='Subtítulo CTA Final')),
                ('contact_email', models.EmailField(default='contato@simdcconr01.com.br', verbose_name='Email de Contato')),
                ('meta_description', models.TextField(blank=True, max_length=300, verbose_name='Meta Description SEO')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={'verbose_name': 'Configuração da Landing Page'},
        ),
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_name', models.CharField(max_length=100, verbose_name='Nome do Autor')),
                ('author_role', models.CharField(blank=True, max_length=100, verbose_name='Cargo')),
                ('author_company', models.CharField(blank=True, max_length=100, verbose_name='Empresa')),
                ('content', models.TextField(verbose_name='Depoimento')),
                ('rating', models.IntegerField(default=5, verbose_name='Nota (1-5)')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='testimonials/', verbose_name='Foto')),
                ('is_approved', models.BooleanField(default=False, verbose_name='Aprovado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Enviado em')),
            ],
            options={'verbose_name': 'Depoimento', 'verbose_name_plural': 'Depoimentos', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título')),
                ('content', models.TextField(verbose_name='Conteúdo')),
                ('announcement_type', models.CharField(choices=[('INFO', 'Informação'), ('WARNING', 'Alerta'), ('SUCCESS', 'Destaque positivo'), ('PROMO', 'Promoção')], default='INFO', max_length=20, verbose_name='Tipo')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expira em')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user', verbose_name='Criado por')),
            ],
            options={'verbose_name': 'Aviso', 'verbose_name_plural': 'Avisos', 'ordering': ['-created_at']},
        ),
    ]
