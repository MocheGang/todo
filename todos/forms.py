from django import forms
from .models import Todo, Page

class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['title', 'description', 'color']

class TodoForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    class Meta:
        model = Todo
        fields = ['title', 'description', 'priority', 'due_date', 'position', 'completed']
