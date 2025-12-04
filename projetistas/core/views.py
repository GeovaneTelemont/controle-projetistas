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
import json
from django.shortcuts import render
from django.db.models import Count, Q
from .models import Producao, TipoProjeto, User
from datetime import datetime, timedelta
from django.utils import timezone

def home(request):
    """
    View para a página inicial.
    """
    # Obter parâmetros
    data_filtro = request.GET.get('data_filtro')
    ver_todos = request.GET.get('ver_todos', 'false')  # Novo parâmetro com valor padrão
    
    # Converter para booleano
    if ver_todos.lower() == 'true':
        ver_todos = True
    else:
        ver_todos = False
    
    # Para superusuários, sempre mostrar todos
    if request.user.is_superuser:
        ver_todos = True
    
    # Base query com filtro de data se existir
    if data_filtro:
        try:
            data_filtro_obj = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            if request.user.is_authenticated and not ver_todos:
                # Usuário comum vendo apenas seus projetos
                producoes = Producao.objects.filter(
                    projetista=request.user,
                    data=data_filtro_obj
                ).order_by('-data')
                base_query = Producao.objects.filter(
                    projetista=request.user,
                    data=data_filtro_obj
                )
            else:
                # Superusuário ou usuário comum escolhendo ver todos
                producoes = Producao.objects.filter(
                    data=data_filtro_obj
                ).order_by('-data')
                base_query = Producao.objects.filter(data=data_filtro_obj)
        except ValueError:
            # Data inválida, usar sem filtro
            if request.user.is_authenticated and not ver_todos:
                producoes = Producao.objects.filter(projetista=request.user).order_by('-data')
                base_query = Producao.objects.filter(projetista=request.user)
            else:
                producoes = Producao.objects.all().order_by('-data')
                base_query = Producao.objects.all()
    else:
        if request.user.is_authenticated and not ver_todos:
            producoes = Producao.objects.filter(projetista=request.user).order_by('-data')
            base_query = Producao.objects.filter(projetista=request.user)
        else:
            producoes = Producao.objects.all().order_by('-data')
            base_query = Producao.objects.all()

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

    # DADOS PARA A TABELA DE PROJETISTAS POR TIPO
    # Buscar todos os tipos de projeto
    tipos_projeto = TipoProjeto.objects.all().order_by('nome')
    
    # Buscar contagem por projetista e tipo
    projetos_por_tipo = base_query.values(
        'projetista__id',
        'projetista__username',
        'projetista__first_name',
        'projetista__last_name',
        'tipo_projeto__nome'
    ).annotate(
        count=Count('id')
    ).order_by('projetista__first_name', 'projetista__last_name')
    
    # Estruturar dados
    projetistas_data = []
    totais_por_tipo = {}
    projetistas_dict = {}
    
    for item in projetos_por_tipo:
        projetista_id = item['projetista__id']
        
        if projetista_id not in projetistas_dict:
            # Criar novo projetista
            nome = f"{item['projetista__first_name']} {item['projetista__last_name']}".strip()
            if not nome:
                nome = item['projetista__username']
            
            projetistas_dict[projetista_id] = {
                'id': projetista_id,
                'username': item['projetista__username'],
                'nome': nome,
                'tipos': {},
                'total': 0
            }
        
        tipo_nome = item['tipo_projeto__nome']
        count = item['count']
        
        # Adicionar contagem ao tipo
        projetistas_dict[projetista_id]['tipos'][tipo_nome] = count
        projetistas_dict[projetista_id]['total'] += count
        
        # Atualizar total por tipo
        if tipo_nome in totais_por_tipo:
            totais_por_tipo[tipo_nome] += count
        else:
            totais_por_tipo[tipo_nome] = count
    
    # Converter dicionário para lista e ordenar
    projetistas_data = list(projetistas_dict.values())
    projetistas_data.sort(key=lambda x: x['total'], reverse=True)
    
    # Calcular totais
    total_geral = sum(proj['total'] for proj in projetistas_data)
    
    # Calcular média
    if projetistas_data:
        media_por_projetista = total_geral / len(projetistas_data)
    else:
        media_por_projetista = 0

    # ========== DADOS PARA O COMPONENTE ANALYTICS ==========
    
    # Período para analytics (últimos 30 dias)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Base query para analytics
    if request.user.is_authenticated and not ver_todos:
        # Usuário vendo apenas seus projetos
        analytics_base_query = Producao.objects.filter(
            projetista=request.user,
            data_inicio__gte=thirty_days_ago
        )
    else:
        # Ver todos os projetos
        analytics_base_query = Producao.objects.filter(
            data_inicio__gte=thirty_days_ago
        )
    
    # Aplicar filtro de data se existir (o mesmo da tabela)
    if data_filtro:
        try:
            data_filtro_obj = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            analytics_base_query = analytics_base_query.filter(data=data_filtro_obj)
        except ValueError:
            pass  # Ignora data inválida para analytics
    
    # 1. Dados para o gráfico por tipo de projeto
    project_types_data = analytics_base_query.values(
        'tipo_projeto__id', 'tipo_projeto__nome'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Cores para o gráfico
    colors = ["#4361ee", "#3a0ca3", "#7209b7", "#f72585", "#4cc9f0", 
              "#4895ef", "#560bad", "#b5179e", "#f15bb5", "#00bbf9"]
    
    analytics_project_types = []
    for i, item in enumerate(project_types_data):
        color = colors[i % len(colors)] if i < len(colors) else f"#{i:06x}"
        analytics_project_types.append({
            'id': item['tipo_projeto__id'],
            'name': item['tipo_projeto__nome'],
            'count': item['count'],
            'color': color
        })
    
    # 2. Dados para o ranking de projetistas
    if request.user.is_authenticated and not ver_todos:
        # Usuário vendo apenas seus projetos - mostra apenas ele no ranking
        designers_query = User.objects.filter(id=request.user.id)
    else:
        # Ver todos os projetistas
        designers_query = User.objects.filter(
            producao__data_inicio__gte=thirty_days_ago
        ).distinct()
    
    # Aplicar filtro de data se existir
    if data_filtro:
        try:
            data_filtro_obj = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            designers_query = designers_query.filter(
                producao__data=data_filtro_obj
            ).distinct()
        except ValueError:
            pass
    
    # Anotar estatísticas
    designers_annotated = designers_query.annotate(
        completed=Count('producao', filter=Q(
            producao__status='CONCLUIDO',
            producao__data_inicio__gte=thirty_days_ago
        )),
        in_progress=Count('producao', filter=Q(
            producao__status='EM_ANDAMENTO',
            producao__data_inicio__gte=thirty_days_ago
        )),
        total=Count('producao', filter=Q(
            producao__data_inicio__gte=thirty_days_ago
        ))
    ).filter(total__gt=0).order_by('-completed')
    
    # Processar dados dos projetistas
    analytics_designers = []
    for designer in designers_annotated:
        if designer.total > 0:
            efficiency = round((designer.completed / designer.total) * 100, 1)
        else:
            efficiency = 0
        
        # Formatar nome
        display_name = designer.get_full_name()
        if not display_name:
            display_name = designer.username
        
        analytics_designers.append({
            'id': designer.id,
            'name': display_name,
            'username': designer.username,
            'completed': designer.completed,
            'in_progress': designer.in_progress,
            'total': designer.total,
            'efficiency': efficiency
        })
    
    # 3. Estatísticas gerais para analytics
    analytics_stats = {
        'total': analytics_base_query.count(),
        'in_progress': analytics_base_query.filter(status='EM_ANDAMENTO').count(),
        'completed': analytics_base_query.filter(status='CONCLUIDO').count(),
    }
    
    # Converter dados para JSON (para usar no template mais facilmente)
    analytics_data_json = {
        'project_types': analytics_project_types,
        'designers': analytics_designers,
        'stats': analytics_stats
    }

    context = {
        'producoes': producoes,
        'stats': stats_dict,
        # Dados para a tabela
        'tipos_projeto': tipos_projeto,
        'projetistas_data': projetistas_data,
        'totais_por_tipo': totais_por_tipo,
        'total_geral': total_geral,
        'media_por_projetista': media_por_projetista,
        # Passar os filtros para o template
        'data_filtro': data_filtro,
        'ver_todos': ver_todos,
        
        # ========== DADOS PARA ANALYTICS ==========
        'analytics_project_types': analytics_project_types,
        'analytics_designers': analytics_designers,
        'analytics_stats': analytics_stats,
        'analytics_data_json': json.dumps(analytics_data_json),  # Dados em JSON
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