from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Producao, TipoProjeto, Categoria, Profile

# Define um admin inline para o Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfis'

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
    list_display = ('dc_id', 'projetista', 'tipo_projeto', 'categoria', 'status', 'motivo_status', 'data', 'updated_at')
    search_fields = ('dc_id', 'projetista__username', 'tipo_projeto__nome', 'categoria__nome')
    list_filter = ('status', 'projetista', 'tipo_projeto', 'categoria', 'data')
    date_hierarchy = 'data'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Informações Principais', {
            'fields': ('data', 'projetista', 'dc_id', ('status', 'motivo_status'))
        }),
        ('Detalhes do Projeto', {
            'fields': ('tipo_projeto', 'categoria', 'metragem_cabo', 'observacoes')
        }),
        ('Datas de Controle', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
