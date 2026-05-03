from django.db import models
from django.contrib.auth.models import User


# =====================================================
# ENUMS
# =====================================================
class EventStatus(models.TextChoices):
    CREATED = "created", "Created"
    ACCEPTED = "accepted", "Accepted"
    ANNOUNCED = "announced", "Announced"
    COMPLETED = "completed", "Completed"


class ProposalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class ExperienceLevel(models.TextChoices):
    EXCELLENT = "excellent", "Excellent"
    GOOD = "good", "Good"
    AVERAGE = "average", "Average"
    POOR = "poor", "Poor"


class RegistrationStatus(models.TextChoices):
    REGISTERED = "registered", "Registered"
    CANCELLED = "cancelled", "Cancelled"
    ATTENDED = "attended", "Attended"


# =====================================================
# CATEGORY
# =====================================================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# =====================================================
# EVENT
# =====================================================
class Event(models.Model):
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
        choices=EventStatus.choices,
        default=EventStatus.CREATED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


# =====================================================
# EVENT PROPOSAL
# =====================================================
class EventProposal(models.Model):
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
        choices=ProposalStatus.choices,
        default=ProposalStatus.PENDING
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.event.name} - {self.organizer.username}"


# =====================================================
# REGISTRATION
# =====================================================
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
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.REGISTERED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'student'],
                name='unique_event_student_registration'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_name} - {self.event.name}"


# =====================================================
# ANNOUNCEMENT
# =====================================================
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


# =====================================================
# NOTIFICATION
# =====================================================
class Notification(models.Model):

    NOTIF_TYPES = [
        ('event_assigned', 'Event Assigned'),
        ('event_announced', 'Event Announced'),
        ('event_completed', 'Event Completed'),
        ('announcement', 'Announcement'),
        ('feedback', 'Feedback'),
        ('general', 'General'),
    ]

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

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIF_TYPES,
        default='general'
    )

    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"


# =====================================================
# FEEDBACK
# =====================================================
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

    rating = models.IntegerField(null=True, blank=True)

    experience = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.GOOD
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'event'],
                name='unique_feedback_per_student_event'
            )
        ]

    def __str__(self):
        return f"{self.student.username} - {self.event.name}"


# =====================================================
# EVENT REPORT (MANUAL SYSTEM - FINAL)
# =====================================================
class EventReport(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True
    )

    name = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name