from django.db import models
from django.conf import settings


AVATAR_COLORS = [
    ('purple', 'Purple'),
    ('pink', 'Pink'),
    ('green', 'Green'),
    ('gold', 'Gold'),
    ('blue', 'Blue'),
]

CATEGORY_CHOICES = [
    ('identity', 'Identity'),
    ('medical', 'Medical'),
    ('education', 'Education'),
    ('finance', 'Finance'),
    ('other', 'Other'),
]

CATEGORY_META = {
    'identity':  {'emoji': '🪪', 'label': 'Identity'},
    'medical':   {'emoji': '🏥', 'label': 'Medical'},
    'education': {'emoji': '🎓', 'label': 'Education'},
    'finance':   {'emoji': '💰', 'label': 'Finance'},
    'other':     {'emoji': '📄', 'label': 'Other'},
}

FILE_TYPE_CHOICES = [
    ('image', 'Image'),
    ('pdf', 'PDF'),
    ('word', 'Word Document'),
]

FILE_TYPE_ICONS = {
    'image': '🖼️',
    'pdf':   '📄',
    'word':  '📝',
}


class FamilyMember(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='family_members',
        null=True, blank=True,
    )
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=50)
    avatar_letter = models.CharField(max_length=3, blank=True)
    avatar_color = models.CharField(max_length=20, choices=AVATAR_COLORS, default='purple')
    photo = models.ImageField(upload_to='avatars/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.display_name} ({self.name})"

    def get_initials(self):
        """Auto-generate 2-letter initials from name, or use avatar_letter if set."""
        if self.avatar_letter:
            return self.avatar_letter.upper()
        parts = self.name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif parts:
            return parts[0][:2].upper()
        return '?'

    def doc_count(self):
        return self.documents.count()

    def category_counts(self):
        return {cat: self.documents.filter(category=cat).count() for cat, _ in CATEGORY_CHOICES}


class Document(models.Model):
    member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE, related_name='documents')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    name = models.CharField(max_length=200)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='image')
    drive_file_id = models.CharField(max_length=200, blank=True)
    drive_view_url = models.URLField(blank=True)
    file_size = models.BigIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.member.display_name} — {self.name}"

    def category_emoji(self):
        return CATEGORY_META.get(self.category, {}).get('emoji', '📄')

    def category_label(self):
        return CATEGORY_META.get(self.category, {}).get('label', 'Other')

    def file_type_icon(self):
        return FILE_TYPE_ICONS.get(self.file_type, '📄')

    def file_size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.0f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def drive_thumbnail_url(self):
        if self.drive_file_id:
            return f"https://drive.google.com/thumbnail?id={self.drive_file_id}&sz=w400"
        return None

    def drive_preview_url(self):
        # Works for images, PDFs, and Word docs (Google Drive renders all)
        if self.drive_file_id:
            return f"https://drive.google.com/file/d/{self.drive_file_id}/preview"
        return None
