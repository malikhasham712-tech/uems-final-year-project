# Generated for proposal date support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0032_eventmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventproposal',
            name='proposed_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
