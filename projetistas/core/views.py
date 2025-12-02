from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Producao
from .forms import CustomUserCreationForm
from django.contrib.auth import logout
from django.contrib import messages
from django import template
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash
from .models import Producao, TipoProjeto, Categoria
from django.utils import timezone
# Mantenha suas outras views como estão (custom_logout, custom_login, cadastro, home)

register = template.Library()

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone

# Adicione esta função junto com suas outras views
def exportar_excel(request):
    """
    View para exportar relatório em Excel com tempo formatado em dias, horas e tempo total
    """
    if not request.user.is_superuser:
        return HttpResponse('Acesso negado', status=403)
    
    # Obter filtros da query string
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    projetista_id = request.GET.get('projetista')
    status = request.GET.get('status')
    
    # Query base - importe o modelo Producao se necessário
    from .models import Producao  # Ajuste conforme a localização do seu modelo
    
    queryset = Producao.objects.all().select_related(
        'projetista', 'tipo_projeto', 'categoria'
    ).prefetch_related('historico')
    
    # Aplicar filtros
    if data_inicio:
        queryset = queryset.filter(data__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data__lte=data_fim)
    if projetista_id:
        queryset = queryset.filter(projetista_id=projetista_id)
    if status:
        queryset = queryset.filter(status=status)
    
    # Ordenar por projetista e data
    queryset = queryset.order_by('projetista__username', '-data')
    
    # Criar workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Produção por Projetista"
    
    # Definir estilos
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    body_font = Font(name='Arial', size=10)
    body_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Função para calcular e formatar tempo
    def calcular_tempo_formatado(data_inicio, data_fim):
        """
        Retorna (dias, horas_minutos, tempo_total)
        Ex: (2, "05:30", "2 dias 05:30")
        """
        if not data_inicio or not data_fim:
            return (0, "00:00", "")
        
        # Calcular diferença em segundos
        delta = data_fim - data_inicio
        segundos_totais = delta.total_seconds()
        
        # Calcular dias inteiros
        dias = int(segundos_totais // (24 * 3600))
        
        # Calcular horas e minutos restantes
        segundos_restantes = segundos_totais % (24 * 3600)
        horas = int(segundos_restantes // 3600)
        minutos = int((segundos_restantes % 3600) // 60)
        
        # Formatar horas:minutos
        horas_minutos = f"{horas:02d}:{minutos:02d}"
        
        # Formatar tempo total
        if dias > 0:
            tempo_total = f"{dias} dia(s) {horas:02d}:{minutos:02d}"
        else:
            tempo_total = f"{horas:02d}:{minutos:02d}"
        
        return (dias, horas_minutos, tempo_total)
    
    # Cabeçalhos
    headers = [
        'DC/ID',                    # 1
        'Projetista',               # 2
        'Tipo de Projeto',          # 3
        'Categoria',                # 4
        'Status',                   # 5
        'Motivo do Status',         # 6
        'Metragem (m)',             # 7
        'Data do Projeto',          # 8
        'Data/Hora Início',         # 9
        'Data/Hora Término',        # 10
        'DIAS',                     # 11
        'HORAS',                    # 12
        'TEMPO TOTAL',              # 13
        'Observações Gerais'        # 14
    ]
    
    # Adicionar cabeçalhos
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Preencher dados
    row_num = 2
    for producao in queryset:
        # Determinar data de término baseado no status
        data_termino = None
        
        if producao.status == 'CONCLUIDO':
            data_termino = producao.data_conclusao
        elif producao.status == 'CANCELADO':
            data_termino = producao.data_cancelamento
        
        # Calcular tempo se tiver data de término
        dias = 0
        horas_minutos = "00:00"
        tempo_total_str = ""
        
        if data_termino:
            dias, horas_minutos, tempo_total_str = calcular_tempo_formatado(
                producao.data_inicio, 
                data_termino
            )
        
        # Determinar texto da data de término
        if producao.status == 'CONCLUIDO':
            data_termino_str = producao.data_conclusao.strftime('%d/%m/%Y %H:%M') if producao.data_conclusao else ''
        elif producao.status == 'CANCELADO':
            data_termino_str = producao.data_cancelamento.strftime('%d/%m/%Y %H:%M') if producao.data_cancelamento else ''
        else:
            data_termino_str = 'EM ANDAMENTO'
        
        # Dados da linha
        row_data = [
            producao.dc_id,
            producao.projetista.get_full_name() or producao.projetista.username,
            producao.tipo_projeto.nome if producao.tipo_projeto else '',
            producao.categoria.nome if producao.categoria else '',
            producao.get_status_display(),
            producao.motivo_status or '',
            float(producao.metragem_cabo) if producao.metragem_cabo else 0.0,
            producao.data.strftime('%d/%m/%Y') if producao.data else '',
            producao.data_inicio.strftime('%d/%m/%Y %H:%M') if producao.data_inicio else '',
            data_termino_str,
            dias,
            horas_minutos,
            tempo_total_str,
            producao.observacoes or ''
        ]
        
        # Adicionar linha
        for col_num, cell_value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=cell_value)
            cell.font = body_font
            cell.border = thin_border
            
            # Alinhamentos
            if col_num in [8, 9, 10, 11, 12, 13]:
                cell.alignment = center_alignment
            elif col_num in [5, 7]:
                cell.alignment = center_alignment
            else:
                cell.alignment = body_alignment
            
            # Formatar números
            if col_num == 7:
                cell.number_format = '#,##0.00'
            elif col_num == 11:
                cell.number_format = '0'
        
        row_num += 1
    
    # Ajustar larguras das colunas
    column_widths = {
        'A': 12, 'B': 20, 'C': 20, 'D': 15, 'E': 15,
        'F': 25, 'G': 12, 'H': 12, 'I': 18, 'J': 18,
        'K': 8, 'L': 10, 'M': 20, 'N': 40
    }
    
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    # Congelar painel
    ws.freeze_panes = 'A2'
    
    # Criar resposta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'producao_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response

def custom_logout(request):
    """
    View personalizada para logout com mensagem
    """
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso!')
    return redirect('home')

def custom_login(request):
    """
    View personalizada para login
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo, {username}!')
                
                # Redirecionar para a página que o usuário tentou acessar ou home
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

def cadastro(request):
    """
    View para cadastro de novos usuários
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Fazer login automaticamente após o cadastro
            login(request, user)
            messages.success(request, f'Conta criada com sucesso! Bem-vindo, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/cadastro.html', {'form': form})



@login_required
def perfil(request):
    """
    View para edição do perfil do usuário
    """
    # Obter dados para os selects
    tipos_projeto = TipoProjeto.objects.all().order_by('nome')
    categorias = Categoria.objects.all().order_by('nome')
    projetos = Producao.objects.filter(projetista=request.user).order_by('-data')
    
    if request.method == 'POST':
        # Debug: verificar qual botão foi clicado
        print("POST data:", request.POST)
        
        # Processar NOVO PROJETO
        if 'novo_projeto' in request.POST:
            print("Processando novo projeto...")
            try:
                # Validar dados obrigatórios
                dc_id = request.POST.get('dc_id')
                data = request.POST.get('data')
                tipo_projeto_id = request.POST.get('tipo_projeto')
                categoria_id = request.POST.get('categoria')
                
                if not all([dc_id, data, tipo_projeto_id, categoria_id]):
                    messages.error(request, 'Preencha todos os campos obrigatórios!')
                    return redirect('perfil')
                
                # Criar novo projeto
                projeto = Producao(
                    dc_id=dc_id,
                    data=data,
                    tipo_projeto_id=tipo_projeto_id,
                    categoria_id=categoria_id,
                    metragem_cabo=request.POST.get('metragem_cabo', 0.00) or 0.00,
                    observacoes=request.POST.get('observacoes', ''),
                    projetista=request.user,
                    status='PENDENTE',
                    motivo_status='Projeto criado'
                )
                
                projeto.save()
                print(f"Projeto {projeto.dc_id} salvo com ID: {projeto.id}")
                messages.success(request, f'Projeto {projeto.dc_id} criado com sucesso!')
                return redirect('perfil')
                    
            except Exception as e:
                print(f"Erro ao criar projeto: {str(e)}")
                messages.error(request, f'Erro ao criar projeto: {str(e)}')
        
        # Processar ALTERAÇÃO DE SENHA
        elif 'change_password' in request.POST:
            print("Processando alteração de senha...")
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Senha alterada com sucesso!')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
            return redirect('perfil')
        
        # Processar ATUALIZAÇÃO DE PERFIL
        elif 'update_profile' in request.POST:
            print("Processando atualização de perfil...")
            try:
                user = request.user
                user.username = request.POST.get('username', user.username)
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.email = request.POST.get('email', user.email)
                user.save()
                messages.success(request, 'Perfil atualizado com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar perfil: {str(e)}')
            return redirect('perfil')
        
        # Processar ALTERAÇÃO DE STATUS
        elif 'alterar_status' in request.POST:
            print("Processando alteração de status...")
            try:
                projeto_id = request.POST.get('projeto_id')
                projeto = Producao.objects.get(id=projeto_id, projetista=request.user)
                projeto.status = request.POST.get('novo_status')
                projeto.motivo_status = request.POST.get('motivo_status', '')
                projeto.save()
                messages.success(request, f'Status do projeto {projeto.dc_id} atualizado!')
            except Producao.DoesNotExist:
                messages.error(request, 'Projeto não encontrado!')
            except Exception as e:
                messages.error(request, f'Erro: {str(e)}')
            return redirect('perfil')
        
        # Processar EDIÇÃO DE PROJETO
        elif 'editar_projeto' in request.POST:
            print("Processando edição de projeto...")
            try:
                projeto_id = request.POST.get('projeto_id')
                projeto = Producao.objects.get(id=projeto_id, projetista=request.user)
                projeto.metragem_cabo = request.POST.get('metragem_cabo', 0.00) or 0.00
                projeto.observacoes = request.POST.get('observacoes', '')
                projeto.save()
                messages.success(request, f'Projeto {projeto.dc_id} atualizado!')
            except Producao.DoesNotExist:
                messages.error(request, 'Projeto não encontrado!')
            except Exception as e:
                messages.error(request, f'Erro: {str(e)}')
            return redirect('perfil')
    
    # Contexto para o template
    context = {
        'tipos_projeto': tipos_projeto,
        'categorias': categorias,
        'projetos': projetos,
    }
    
    return render(request, 'registration/perfil.html', context)

def home(request):
    """
    View para a página inicial.
    """
    if request.user.is_authenticated and not request.user.is_superuser:
        producoes = Producao.objects.filter(projetista=request.user).order_by('-data')
    else:
        producoes = Producao.objects.all().order_by('-data')

    # Cálculo das estatísticas
    stats_query = producoes.values('status').annotate(total=Count('id'))
    
    stats_dict = {
        'PENDENTE': 0,
        'EM_ANDAMENTO': 0,
        'REVISAO': 0,
        'CONCLUIDO': 0,
        'CANCELADO': 0,
        'total': 0
    }
    
    for stat in stats_query:
        stats_dict[stat['status']] = stat['total']
        stats_dict['total'] += stat['total']

    producoes = producoes.select_related(
        'projetista', 'tipo_projeto', 'categoria'
    ).prefetch_related('historico')

    context = {
        'producoes': producoes,
        'stats': stats_dict,
    }

    return render(request, 'home.html', context)


@register.filter
def calcular_percentual(valor, total):
    """Calcula o percentual de um valor em relação ao total"""
    if total and total > 0:
        return (valor / total) * 100
    return 0

@register.filter
def get_item(dictionary, key):
    """Retorna um item de um dicionário pela chave"""
    return dictionary.get(key, 0) 