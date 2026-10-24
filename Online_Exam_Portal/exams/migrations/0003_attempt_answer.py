from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('exams', '0002_question'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('in_progress', 'In progress'), ('submitted', 'Submitted')], default='in_progress', max_length=12)),
                ('score', models.PositiveIntegerField(blank=True, null=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='exams.exam')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_attempts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_option', models.CharField(blank=True, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1, null=True)),
                ('marked_for_review', models.BooleanField(default=False)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='exams.attempt')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_answers', to='exams.question')),
            ],
        ),
        migrations.AddConstraint(model_name='attempt', constraint=models.UniqueConstraint(fields=('exam', 'student'), name='unique_student_exam_attempt')),
        migrations.AddConstraint(model_name='answer', constraint=models.UniqueConstraint(fields=('attempt', 'question'), name='unique_attempt_question_answer')),
    ]
