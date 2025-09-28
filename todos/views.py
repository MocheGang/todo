from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Todo

def todo_list(request):
    todos = Todo.objects.all()
    return render(request, 'todos/list.html', {'todos': todos})

def add_todo(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST.get('description', '')
        Todo.objects.create(title=title, description=description)
        return redirect('todo_list')
    return render(request, 'todos/add.html')

def toggle_todo(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)
    todo.completed = not todo.completed
    todo.save()
    return redirect('todo_list')

def delete_todo(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)
    todo.delete()
    return redirect('todo_list')
# Create your views here.
