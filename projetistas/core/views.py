from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Producao
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm
# views.py
from django.contrib.auth import logout
from django.contrib import messages

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

# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from .models import Producao, TipoProjeto, Categoria, Profile
from django.contrib.auth.models import User

# Mantenha suas outras views como estão (custom_logout, custom_login, cadastro, home)

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