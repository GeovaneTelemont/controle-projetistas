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

@login_required
def perfil(request):
    """
    View para edição do perfil do usuário
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('perfil')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
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