from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from .forms import SignUpForm

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # connexion auto après inscription
            return redirect("todo_list")  # redirige vers la liste des pages Todo
    else:
        form = SignUpForm()
    return render(request, "auth/signup.html", {"form": form})

class CustomLoginView(LoginView):
    template_name = "auth/login.html"

class CustomLogoutView(LogoutView):
    template_name = "auth/logout.html"
