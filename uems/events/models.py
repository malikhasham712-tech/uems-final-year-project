from django.db import models
from django.contrib.auth.models import User


# ----------------------
# CATEGORY
# ----------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# ----------------------
# EVENT
# ----------------------
class Event(models.Model):

    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('Accepted', 'Accepted'),
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

    venue = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Created'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


# ----------------------
# PROPOSAL
# ----------------------
class EventProposal(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
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
    requirements = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.event.name} - {self.organizer.username}"


# ----------------------
# REGISTRATION
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

    status = models.CharField(
        max_length=20,
        default="registered"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'student')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_name} - {self.event.name}"


# ----------------------
# ANNOUNCEMENT
# ----------------------
class Announcement(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='announcements'
    )

    message = models.TextField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_announcements"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Announcement - {self.event.name}"


# ----------------------
# NOTIFICATION
# ----------------------
class Notification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    message = models.TextField()
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} Notification"


# ----------------------
# FEEDBACK
# ----------------------
class Feedback(models.Model):

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    message = models.TextField()
    rating = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('student', 'event')   # ✅ IMPORTANT FIX

    def __str__(self):
        return f"{self.student.username} - {self.event.name}"