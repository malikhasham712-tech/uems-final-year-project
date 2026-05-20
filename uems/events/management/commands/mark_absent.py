from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event, EventRegistration, Attendance


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        today = timezone.now().date()

        events = Event.objects.filter(date=today)

        for event in events:

            registrations = EventRegistration.objects.filter(event=event)

            for reg in registrations:

                exists = Attendance.objects.filter(
                    event=event,
                    student=reg.student
                ).exists()

                if not exists:

                    Attendance.objects.create(
                        event=event,
                        student=reg.student,
                        status="absent"
                    )

        self.stdout.write("✅ Absent marking completed")