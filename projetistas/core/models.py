from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils import timezone

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

    # Novos campos para controle de datas
    data_inicio = models.DateTimeField('Data de Início', auto_now_add=True)
    data_conclusao = models.DateTimeField('Data de Conclusão', null=True, blank=True)
    data_cancelamento = models.DateTimeField('Data de Cancelamento', null=True, blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Produção'
        verbose_name_plural = 'Produções'
        ordering = ['-data']

    def __str__(self):
        return f'{self.dc_id} - {self.projetista}'

    def save(self, *args, **kwargs):
        # Verifica se é uma nova instância
        if not self.pk:
            # Nova produção - data_inicio já é definida automaticamente
            super().save(*args, **kwargs)
            # Cria o primeiro registro no histórico
            HistoricoStatus.objects.create(
                producao=self,
                status=self.status,
                motivo=self.motivo_status
            )
        else:
            # Verifica se o status foi alterado
            old_instance = Producao.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                # Atualiza datas especiais baseadas no status
                if self.status == 'CONCLUIDO' and not self.data_conclusao:
                    self.data_conclusao = timezone.now()
                elif self.status == 'CANCELADO' and not self.data_cancelamento:
                    self.data_cancelamento = timezone.now()
                
                # Cria registro no histórico
                HistoricoStatus.objects.create(
                    producao=self,
                    status=self.status,
                    motivo=self.motivo_status
                )
            
            super().save(*args, **kwargs)

    @property
    def tempo_total(self):
        """Calcula o tempo total desde o início até conclusão/cancelamento ou agora"""
        if self.data_conclusao:
            return self.data_conclusao - self.data_inicio
        elif self.data_cancelamento:
            return self.data_cancelamento - self.data_inicio
        else:
            return timezone.now() - self.data_inicio

    @property
    def tempo_em_andamento(self):
        """Calcula o tempo que ficou em andamento"""
        historico_andamento = self.historico.filter(status='EM_ANDAMENTO').first()
        if historico_andamento:
            proximo_status = self.historico.filter(
                data_alteracao__gt=historico_andamento.data_alteracao
            ).first()
            if proximo_status:
                return proximo_status.data_alteracao - historico_andamento.data_alteracao
        return None

    def get_historico_ordenado(self):
        """Retorna o histórico ordenado por data"""
        return self.historico.all().order_by('data_alteracao')

class HistoricoStatus(models.Model):
    """
    Modelo para registrar o histórico de alterações de status.
    """
    producao = models.ForeignKey(
        Producao, 
        on_delete=models.CASCADE, 
        related_name='historico',
        verbose_name='Produção'
    )
    status = models.CharField(
        'Status', 
        max_length=20, 
        choices=Producao.STATUS_CHOICES
    )
    motivo = models.CharField(
        'Motivo/Observação', 
        max_length=255, 
        blank=True
    )
    data_alteracao = models.DateTimeField(
        'Data da Alteração', 
        auto_now_add=True
    )
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Usuário que alterou'
    )

    class Meta:
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Históricos de Status'
        ordering = ['-data_alteracao']

    def __str__(self):
        return f'{self.producao.dc_id} - {self.get_status_display()} - {self.data_alteracao.strftime("%d/%m/%Y %H:%M")}'

    def save(self, *args, **kwargs):
        # Se não foi passado um usuário, tenta pegar do contexto da request
        if not self.usuario and hasattr(self, '_request_user'):
            self.usuario = self._request_user
        super().save(*args, **kwargs)