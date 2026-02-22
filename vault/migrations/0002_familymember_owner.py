from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_to_first_user(apps, schema_editor):
    """Assign existing family members to the first superuser."""
    User = apps.get_model('auth', 'User')
    FamilyMember = apps.get_model('vault', 'FamilyMember')
    first_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if first_user:
        FamilyMember.objects.filter(owner=None).update(owner=first_user)


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='familymember',
            name='owner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='family_members',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(assign_to_first_user, migrations.RunPython.noop),
    ]
