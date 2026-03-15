from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Event(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
    ]
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organized_events"
    )
    venue = models.CharField(max_length=200)  # Added venue field
    date = models.DateField(null=True, blank=True)  # Added date field
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EventProposal(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="proposals")
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="proposals")
    proposed_venue = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event.name} - {self.organizer.username}"