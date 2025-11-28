from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Create your models here.
class TipoProjeto(models.Model):
    """
    Modelo para cadastrar os tipos de projeto.
    """
    nome = models.CharField('Nome', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Tipo de Projeto'
        verbose_name_plural = 'Tipos de Projetos'

    def __str__(self):
        return self.nome

class Categoria(models.Model):
    """
    Modelo para cadastrar as categorias dos projetos.
    """
    nome = models.CharField('Nome', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nome

class Profile(models.Model):
    """
    Perfil de usuário para estender o modelo User padrão do Django.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    must_change_password = models.BooleanField('Forçar troca de senha', default=True)

    def __str__(self):
        return self.user.username

# Signal para criar ou atualizar o perfil do usuário automaticamente.
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
post_save.connect(create_or_update_user_profile, sender=User)

class Producao(models.Model):
    """
    Modelo para registrar a produção dos projetistas.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('REVISAO', 'Revisão'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]

    data = models.DateField('Data')
    projetista = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Projetista')
    tipo_projeto = models.ForeignKey(TipoProjeto, on_delete=models.PROTECT, verbose_name='Tipo de Projeto')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name='Categoria')
    dc_id = models.CharField('DC/ID', max_length=50, unique=True)
    metragem_cabo = models.DecimalField('Metragem de Cabo', max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    motivo_status = models.CharField('Motivo/Observação do Status', max_length=255, blank=True, help_text='Ex: Motivo da pendência, do cancelamento ou em que etapa está o andamento.')
    observacoes = models.TextField('Observações', blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Produção'
        verbose_name_plural = 'Produções'
        ordering = ['-data']

    def __str__(self):
        return f'{self.dc_id} - {self.projetista}'
