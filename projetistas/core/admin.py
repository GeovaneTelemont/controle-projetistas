from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Producao, TipoProjeto, Categoria, Profile, HistoricoStatus

# Define um admin inline para o Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfis'

# Admin Inline para o Histórico de Status
class HistoricoStatusInline(admin.TabularInline):
    model = HistoricoStatus
    extra = 0
    readonly_fields = ('data_alteracao', 'status', 'motivo', 'usuario')
    can_delete = False
    max_num = 0  # Não permite adicionar novos pelo admin (só via sistema)
    
    def has_add_permission(self, request, obj=None):
        return False

# Register your models here.
@admin.register(TipoProjeto)
class TipoProjetoAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para Tipos de Projeto.
    """
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para Categorias.
    """
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(HistoricoStatus)
class HistoricoStatusAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para Histórico de Status.
    """
    list_display = ('producao', 'status_display', 'data_alteracao', 'usuario_display', 'motivo_resumido')
    list_filter = ('status', 'data_alteracao', 'usuario')
    search_fields = ('producao__dc_id', 'motivo', 'usuario__username')
    readonly_fields = ('data_alteracao',)
    date_hierarchy = 'data_alteracao'
    
    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Status'
    
    def usuario_display(self, obj):
        return obj.usuario.get_full_name() if obj.usuario else 'Sistema'
    usuario_display.short_description = 'Usuário'
    
    def motivo_resumido(self, obj):
        return obj.motivo[:50] + '...' if len(obj.motivo) > 50 else obj.motivo
    motivo_resumido.short_description = 'Motivo'

# Redefine o User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# Re-registra o User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Producao)
class ProducaoAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para o modelo Producao.
    """
    list_display = ('dc_id', 'projetista', 'tipo_projeto', 'categoria', 'status_display', 'data_inicio_formatada', 'data_conclusao_formatada', 'tempo_total_display')
    search_fields = ('dc_id', 'projetista__username', 'tipo_projeto__nome', 'categoria__nome')
    list_filter = ('status', 'projetista', 'tipo_projeto', 'categoria', 'data', 'data_inicio')
    date_hierarchy = 'data_inicio'
    readonly_fields = ('created_at', 'updated_at', 'data_inicio', 'data_conclusao', 'data_cancelamento', 'historico_table')
    inlines = [HistoricoStatusInline]
    
    fieldsets = (
        ('Informações Principais', {
            'fields': ('data', 'projetista', 'dc_id', ('status', 'motivo_status'))
        }),
        ('Detalhes do Projeto', {
            'fields': ('tipo_projeto', 'categoria', 'metragem_cabo', 'observacoes')
        }),
        ('Datas de Controle', {
            'fields': ('data_inicio', 'data_conclusao', 'data_cancelamento', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Histórico de Status', {
            'fields': ('historico_table',),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        status_colors = {
            'PENDENTE': 'orange',
            'EM_ANDAMENTO': 'blue',
            'REVISAO': 'purple',
            'CONCLUIDO': 'green',
            'CANCELADO': 'red',
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def data_inicio_formatada(self, obj):
        return obj.data_inicio.strftime("%d/%m/%Y %H:%M") if obj.data_inicio else "-"
    data_inicio_formatada.short_description = 'Início'
    data_inicio_formatada.admin_order_field = 'data_inicio'
    
    def data_conclusao_formatada(self, obj):
        return obj.data_conclusao.strftime("%d/%m/%Y %H:%M") if obj.data_conclusao else "-"
    data_conclusao_formatada.short_description = 'Conclusão'
    data_conclusao_formatada.admin_order_field = 'data_conclusao'
    
    def tempo_total_display(self, obj):
        tempo = obj.tempo_total
        if tempo:
            dias = tempo.days
            horas = tempo.seconds // 3600
            if dias > 0:
                return f"{dias}d {horas}h"
            return f"{horas}h"
        return "-"
    tempo_total_display.short_description = 'Tempo Total'
    
    def historico_table(self, obj):
        historico = obj.get_historico_ordenado()
        if not historico:
            return "Nenhum registro no histórico"
        
        rows = []
        for registro in historico:
            row = f"""
            <tr>
                <td>{registro.data_alteracao.strftime("%d/%m/%Y %H:%M")}</td>
                <td><strong>{registro.get_status_display()}</strong></td>
                <td>{registro.motivo or '-'}</td>
                <td>{registro.usuario.get_full_name() if registro.usuario else 'Sistema'}</td>
            </tr>
            """
            rows.append(row)
        
        table = f"""
        <div style="max-height: 400px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Data/Hora</th>
                        <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Status</th>
                        <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Motivo</th>
                        <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Usuário</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """
        return format_html(table)
    historico_table.short_description = 'Histórico Completo'
    
    def save_model(self, request, obj, form, change):
        """Sobrescreve o save para registrar o usuário que fez a alteração"""
        if change and 'status' in form.changed_data:
            # Cria registro no histórico quando o status é alterado pelo admin
            HistoricoStatus.objects.create(
                producao=obj,
                status=obj.status,
                motivo=obj.motivo_status,
                usuario=request.user
            )
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Otimiza as queries para o admin"""
        return super().get_queryset(request).select_related(
            'projetista', 'tipo_projeto', 'categoria'
        ).prefetch_related('historico')