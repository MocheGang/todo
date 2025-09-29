# todos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Page, Todo, UserProfile
from django.db.models import Q
import json

# ===== VUES D'AUTHENTIFICATION =====

def register_view(request):
    """Vue pour l'inscription des utilisateurs"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username}!')
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'todos/auth/register.html', {'form': form})

def login_view(request):
    """Vue pour la connexion des utilisateurs"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'todos/auth/login.html')

def logout_view(request):
    """Vue pour la déconnexion"""
    logout(request)
    messages.success(request, 'Vous êtes déconnecté avec succès.')
    return redirect('login')

# ===== VUES PRINCIPALES =====

@login_required
def dashboard(request):
    """Page d'accueil après connexion - tableau de bord"""
    user_pages = Page.objects.filter(owner=request.user, is_active=True)
    
    # Statistiques
    total_pages = user_pages.count()
    total_todos = Todo.objects.filter(page__owner=request.user).count()
    completed_todos = Todo.objects.filter(page__owner=request.user, completed=True).count()
    pending_todos = total_todos - completed_todos
    
    # Pages récentes avec leurs todos
    recent_pages = user_pages[:5]
    for page in recent_pages:
        page.recent_todos = page.todos.all()[:3]
    
    context = {
        'user_pages': user_pages,
        'recent_pages': recent_pages,
        'stats': {
            'total_pages': total_pages,
            'total_todos': total_todos,
            'completed_todos': completed_todos,
            'pending_todos': pending_todos,
        }
    }
    return render(request, 'todos/dashboard.html', context)

# ===== VUES POUR LES PAGES =====

@login_required
def page_list(request):
    """Liste de toutes les pages de l'utilisateur"""
    pages = Page.objects.filter(owner=request.user, is_active=True)
    return render(request, 'todos/pages/list.html', {'pages': pages})

@login_required
def page_create(request):
    """Créer une nouvelle page"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '#007bff')
        
        if title:
            try:
                page = Page.objects.create(
                    title=title,
                    description=description,
                    color=color,
                    owner=request.user
                )
                messages.success(request, f'Page "{title}" créée avec succès!')
                return redirect('page_detail', page_id=page.id)
            except Exception as e:
                messages.error(request, 'Une page avec ce nom existe déjà.')
        else:
            messages.error(request, 'Le titre est obligatoire.')
    
    return render(request, 'todos/pages/create.html')

@login_required
def page_detail(request, page_id):
    """Afficher une page avec tous ses todos"""
    page = get_object_or_404(Page, id=page_id, owner=request.user, is_active=True)
    
    # Filtres
    filter_status = request.GET.get('status', 'all')
    filter_priority = request.GET.get('priority', 'all')
    search_query = request.GET.get('search', '')
    
    # Récupérer tous les todos de la page
    todos = page.todos.all()
    
    # Appliquer les filtres
    if filter_status == 'completed':
        todos = todos.filter(completed=True)
    elif filter_status == 'pending':
        todos = todos.filter(completed=False)
    
    if filter_priority != 'all':
        todos = todos.filter(priority=filter_priority)
    
    if search_query:
        todos = todos.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Statistiques de la page
    page_stats = {
        'total': page.todos.count(),
        'completed': page.todos.filter(completed=True).count(),
        'pending': page.todos.filter(completed=False).count(),
        'overdue': page.todos.filter(due_date__lt=timezone.now(), completed=False).count(),
    }
    
    context = {
        'page': page,
        'todos': todos,
        'page_stats': page_stats,
        'filter_status': filter_status,
        'filter_priority': filter_priority,
        'search_query': search_query,
    }
    return render(request, 'todos/pages/detail.html', context)

@login_required
def page_edit(request, page_id):
    """Modifier une page"""
    page = get_object_or_404(Page, id=page_id, owner=request.user, is_active=True)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '#007bff')
        
        if title:
            try:
                page.title = title
                page.description = description
                page.color = color
                page.save()
                messages.success(request, f'Page "{title}" modifiée avec succès!')
                return redirect('page_detail', page_id=page.id)
            except Exception as e:
                messages.error(request, 'Une page avec ce nom existe déjà.')
        else:
            messages.error(request, 'Le titre est obligatoire.')
    
    return render(request, 'todos/pages/edit.html', {'page': page})

@login_required
def page_delete(request, page_id):
    """Supprimer une page (soft delete)"""
    page = get_object_or_404(Page, id=page_id, owner=request.user, is_active=True)
    
    if request.method == 'POST':
        page.is_active = False
        page.save()
        messages.success(request, f'Page "{page.title}" supprimée avec succès!')
        return redirect('dashboard')
    
    return render(request, 'todos/pages/delete.html', {'page': page})

# ===== VUES POUR LES TODOS =====

@login_required
def todo_create(request, page_id):
    """Créer un nouveau todo dans une page"""
    page = get_object_or_404(Page, id=page_id, owner=request.user, is_active=True)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date')
        
        if title:
            todo = Todo.objects.create(
                title=title,
                description=description,
                priority=priority,
                page=page,
                due_date=due_date if due_date else None
            )
            messages.success(request, f'Tâche "{title}" créée avec succès!')
            return redirect('page_detail', page_id=page.id)
        else:
            messages.error(request, 'Le titre est obligatoire.')
    
    return render(request, 'todos/todos/create.html', {'page': page})

@login_required
def todo_edit(request, todo_id):
    """Modifier un todo"""
    todo = get_object_or_404(Todo, id=todo_id, page__owner=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date')
        
        if title:
            todo.title = title
            todo.description = description
            todo.priority = priority
            todo.due_date = due_date if due_date else None
            todo.save()
            messages.success(request, f'Tâche "{title}" modifiée avec succès!')
            return redirect('page_detail', page_id=todo.page.id)
        else:
            messages.error(request, 'Le titre est obligatoire.')
    
    return render(request, 'todos/todos/edit.html', {'todo': todo})

@login_required
def todo_delete(request, todo_id):
    """Supprimer un todo"""
    todo = get_object_or_404(Todo, id=todo_id, page__owner=request.user)
    page_id = todo.page.id
    
    if request.method == 'POST':
        todo_title = todo.title
        todo.delete()
        messages.success(request, f'Tâche "{todo_title}" supprimée avec succès!')
        return redirect('page_detail', page_id=page_id)
    
    return render(request, 'todos/todos/delete.html', {'todo': todo})

@login_required
@require_POST
def todo_toggle(request, todo_id):
    """Marquer un todo comme complété/non complété (AJAX)"""
    todo = get_object_or_404(Todo, id=todo_id, page__owner=request.user)
    todo.completed = not todo.completed
    todo.save()
    
    return JsonResponse({
        'success': True,
        'completed': todo.completed,
        'message': f'Tâche {"complétée" if todo.completed else "marquée comme non complétée"}'
    })

# ===== VUES AJAX =====

@login_required
def quick_add_todo(request):
    """Ajouter rapidement un todo via AJAX"""
    if request.method == 'POST':
        data = json.loads(request.body)
        page_id = data.get('page_id')
        title = data.get('title')
        
        if page_id and title:
            page = get_object_or_404(Page, id=page_id, owner=request.user, is_active=True)
            todo = Todo.objects.create(
                title=title,
                page=page
            )
            return JsonResponse({
                'success': True,
                'todo': {
                    'id': todo.id,
                    'title': todo.title,
                    'completed': todo.completed,
                    'priority': todo.priority
                }
            })
    
    return JsonResponse({'success': False, 'error': 'Données invalides'})

# ===== VUES DE PROFIL =====

@login_required
def profile_view(request):
    """Afficher et modifier le profil utilisateur"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        profile.bio = request.POST.get('bio', '')
        profile.theme = request.POST.get('theme', 'light')
        profile.notifications_enabled = 'notifications_enabled' in request.POST
        profile.save()
        
        messages.success(request, 'Profil mis à jour avec succès!')
        return redirect('profile')
    
    return render(request, 'todos/profile.html', {'profile': profile})

# ===== VUE DE RECHERCHE GLOBALE =====

@login_required
def search_view(request):
    """Recherche globale dans toutes les pages et todos"""
    query = request.GET.get('q', '')
    results = {
        'pages': [],
        'todos': []
    }
    
    if query:
        results['pages'] = Page.objects.filter(
            owner=request.user,
            is_active=True,
            title__icontains=query
        )[:10]
        
        results['todos'] = Todo.objects.filter(
            page__owner=request.user,
            title__icontains=query
        ).select_related('page')[:20]
    
    context = {
        'query': query,
        'results': results
    }
    return render(request, 'todos/search.html', context)