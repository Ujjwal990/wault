from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0002_familymember_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='familymember',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
        migrations.AlterField(
            model_name='familymember',
            name='avatar_letter',
            field=models.CharField(blank=True, max_length=3),
        ),
        migrations.AlterField(
            model_name='document',
            name='file_type',
            field=models.CharField(
                choices=[('image', 'Image'), ('pdf', 'PDF'), ('word', 'Word Document')],
                default='image', max_length=10,
            ),
        ),
    ]
