# todos/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class Page(models.Model):
    """
    Modèle pour les pages de todo liste
    Chaque utilisateur peut créer plusieurs pages pour organiser ses tâches
    """
    title = models.CharField(max_length=200, verbose_name="Titre de la page")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='pages',
        verbose_name="Propriétaire"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    is_active = models.BooleanField(default=True, verbose_name="Page active")
    
    # Couleur pour personnaliser la page (optionnel)
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text="Couleur en format hexadécimal (ex: #ff0000)",
        verbose_name="Couleur"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        # Un utilisateur ne peut pas avoir deux pages avec le même titre
        unique_together = ['owner', 'title']

    def __str__(self):
        return f"{self.title} - {self.owner.username}"

    def get_absolute_url(self):
        return reverse('page_detail', kwargs={'pk': self.pk})
    
    def get_todos_count(self):
        """Retourne le nombre de todos dans cette page"""
        return self.todos.count()
    
    def get_completed_todos_count(self):
        """Retourne le nombre de todos complétées dans cette page"""
        return self.todos.filter(completed=True).count()
    
    def get_pending_todos_count(self):
        """Retourne le nombre de todos non complétées dans cette page"""
        return self.todos.filter(completed=False).count()


class Todo(models.Model):
    """
    Modèle pour les tâches individuelles
    Chaque tâche appartient à une page et donc à un utilisateur
    """
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    completed = models.BooleanField(default=False, verbose_name="Complétée")
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name="Priorité"
    )
    
    # Relation avec la page (et donc indirectement avec l'utilisateur)
    page = models.ForeignKey(
        Page, 
        on_delete=models.CASCADE, 
        related_name='todos',
        verbose_name="Page"
    )
    
    # Dates
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    due_date = models.DateTimeField(blank=True, null=True, verbose_name="Date d'échéance")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Complétée le")
    
    # Position pour l'ordre des tâches dans une page
    position = models.PositiveIntegerField(default=0, verbose_name="Position")

    class Meta:
        ordering = ['position', '-created_at']
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"

    def __str__(self):
        status = "✓" if self.completed else "○"
        return f"{status} {self.title}"

    def get_absolute_url(self):
        return reverse('todo_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Marquer la date de completion quand la tâche est marquée comme complétée
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Vérifie si la tâche est en retard"""
        if self.due_date and not self.completed:
            return timezone.now() > self.due_date
        return False
    
    @property
    def priority_color(self):
        """Retourne une couleur basée sur la priorité"""
        colors = {
            'low': '#28a745',      # Vert
            'medium': '#ffc107',   # Jaune
            'high': '#fd7e14',     # Orange
            'urgent': '#dc3545',   # Rouge
        }
        return colors.get(self.priority, '#6c757d')


class UserProfile(models.Model):
    """
    Profil utilisateur étendu pour stocker des préférences
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Préférences
    theme = models.CharField(
        max_length=20, 
        choices=[('light', 'Clair'), ('dark', 'Sombre')], 
        default='light',
        verbose_name="Thème"
    )
    
    notifications_enabled = models.BooleanField(
        default=True, 
        verbose_name="Notifications activées"
    )
    
    # Informations supplémentaires
    bio = models.TextField(blank=True, null=True, verbose_name="Biographie")
    
    # Dates
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateur"

    def __str__(self):
        return f"Profil de {self.user.username}"

    def get_total_pages(self):
        """Retourne le nombre total de pages de l'utilisateur"""
        return self.user.pages.filter(is_active=True).count()
    
    def get_total_todos(self):
        """Retourne le nombre total de todos de l'utilisateur"""
        return Todo.objects.filter(page__owner=self.user).count()
    
    def get_completed_todos(self):
        """Retourne le nombre de todos complétées de l'utilisateur"""
        return Todo.objects.filter(page__owner=self.user, completed=True).count()


# Signal pour créer automatiquement un profil utilisateur
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un profil quand un utilisateur est créé"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le profil quand l'utilisateur est sauvegardé"""
    if hasattr(instance, 'profile'):
        instance.profile.save()