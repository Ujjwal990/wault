from django.db import models
from django.utils import timezone


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
]


class FamilyMember(models.Model):
    name = models.CharField(max_length=100)           # Full name e.g. "Rajesh Sharma"
    display_name = models.CharField(max_length=50)    # Short name e.g. "Papa"
    avatar_letter = models.CharField(max_length=2)    # e.g. "R"
    avatar_color = models.CharField(max_length=20, choices=AVATAR_COLORS, default='purple')
    order = models.PositiveIntegerField(default=0)    # Display order
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.display_name} ({self.name})"

    def doc_count(self):
        return self.documents.count()

    def category_counts(self):
        counts = {}
        for cat, _ in CATEGORY_CHOICES:
            counts[cat] = self.documents.filter(category=cat).count()
        return counts


class Document(models.Model):
    member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE, related_name='documents')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    name = models.CharField(max_length=200)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='image')
    drive_file_id = models.CharField(max_length=200, blank=True)
    drive_view_url = models.URLField(blank=True)
    file_size = models.BigIntegerField(default=0)     # bytes
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
        if self.drive_file_id:
            return f"https://drive.google.com/file/d/{self.drive_file_id}/preview"
        return None
