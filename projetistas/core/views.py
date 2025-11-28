from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Producao
from .forms import CustomSetPasswordForm


# Create your views here.
def home(request):
    """
    View para a página inicial.
    - Se o usuário estiver logado, mostra apenas suas produções.
    - Se não estiver logado, mostra todas as produções.
    """
    # Se o usuário estiver logado E NÃO for um superusuário, mostre apenas suas produções.
    if request.user.is_authenticated and not request.user.is_superuser:
        # Este é um projetista comum.
        producoes = Producao.objects.filter(projetista=request.user).order_by('-data')
    else:
        # Para visitantes OU para o superusuário, mostre todas as produções.
        producoes = Producao.objects.all().order_by('-data')

    return render(request, 'home.html', {'producoes': producoes})

@login_required
def change_password(request):
    form = CustomSetPasswordForm(request.user)
    if request.method == 'POST':
        form = CustomSetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Marca que o usuário não precisa mais trocar a senha
            user.profile.must_change_password = False
            user.profile.save()
            return redirect('home')

    return render(request, 'core/change_password.html', {'form': form})
