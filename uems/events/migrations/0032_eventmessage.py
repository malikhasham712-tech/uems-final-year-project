# Generated for event-scoped in-system messaging.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0031_attendance'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EventMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='events.event')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_event_messages', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_event_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
                'indexes': [
                    models.Index(fields=['event', 'sender', 'recipient', 'created_at'], name='evt_msg_thread_idx'),
                    models.Index(fields=['recipient', 'is_read'], name='evt_msg_unread_idx'),
                ],
            },
        ),
    ]
