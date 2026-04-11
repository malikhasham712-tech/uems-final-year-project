from django.db import models
from django.contrib.auth.models import User


# ----------------------
# CATEGORY MODEL
# ----------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# ----------------------
# EVENT MODEL
# ----------------------
class Event(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Announced', 'Announced'),
        ('Completed', 'Completed'),
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

    venue = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,   # ✅ FIXED (important)
        choices=STATUS_CHOICES,
        default='Pending'
    )

    def __str__(self):
        return self.name


# ----------------------
# EVENT PROPOSAL
# ----------------------
class EventProposal(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="proposals"
    )

    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="proposals"
    )

    proposed_venue = models.CharField(max_length=200)
    details = models.TextField(blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    number = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.number:
            last = EventProposal.objects.filter(
                event=self.event
            ).order_by('-number').first()

            self.number = 1 if not last else last.number + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event.name} - {self.organizer.username}"


# ----------------------
# EVENT REGISTRATION
# ----------------------
class EventRegistration(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations"
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE)

    student_name = models.CharField(max_length=100)
    registration_no = models.CharField(max_length=50)
    semester = models.CharField(max_length=20)
    department = models.CharField(max_length=100)
    email = models.EmailField()
    contact_no = models.CharField(max_length=15)

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'student')

    def __str__(self):
        return f"{self.student_name} - {self.event.name}"