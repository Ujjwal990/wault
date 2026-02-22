from django.contrib import admin
from .models import FamilyMember, Document


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'avatar_color', 'doc_count', 'order']
    list_editable = ['order']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'member', 'category', 'file_type', 'file_size_display', 'created_at']
    list_filter = ['member', 'category', 'file_type']
    search_fields = ['name', 'member__name', 'member__display_name']
    readonly_fields = ['drive_file_id', 'drive_view_url', 'file_size', 'created_at', 'updated_at']
