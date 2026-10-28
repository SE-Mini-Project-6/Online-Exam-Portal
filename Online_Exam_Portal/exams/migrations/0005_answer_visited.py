from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('exams', '0004_answer_saved_at'),
    ]

    operations = [
        # Existing rows were created by a student interacting with the question, so they count as visited.
        migrations.AddField(
            model_name='answer',
            name='visited',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='visited',
            field=models.BooleanField(default=False),
        ),
    ]
