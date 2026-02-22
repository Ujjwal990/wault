import io
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.db.models import Q, Count
from django.views.decorators.http import require_POST

from .models import FamilyMember, Document, CATEGORY_CHOICES, CATEGORY_META
from .forms import DocumentUploadForm, FamilyMemberForm, DocumentRenameForm
from . import google_drive


# ── AUTH ──────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome! Your vault is ready.')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# ── HOME ──────────────────────────────────────────

@login_required
def home(request):
    members = FamilyMember.objects.filter(owner=request.user).annotate(
        doc_count_ann=Count('documents')
    )
    recent_docs = Document.objects.filter(
        member__owner=request.user
    ).select_related('member').order_by('-updated_at')[:8]
    total_docs = Document.objects.filter(member__owner=request.user).count()

    query = request.GET.get('q', '').strip()
    search_results = None
    if query:
        search_results = Document.objects.filter(
            member__owner=request.user
        ).select_related('member').filter(
            Q(name__icontains=query) |
            Q(member__display_name__icontains=query) |
            Q(member__name__icontains=query) |
            Q(category__icontains=query) |
            Q(notes__icontains=query)
        )

    return render(request, 'vault/home.html', {
        'members': members,
        'recent_docs': recent_docs,
        'total_docs': total_docs,
        'query': query,
        'search_results': search_results,
    })


# ── MEMBER ────────────────────────────────────────

@login_required
def member_detail(request, pk):
    member = get_object_or_404(FamilyMember, pk=pk, owner=request.user)
    category_filter = request.GET.get('cat', '')
    docs = member.documents.all()
    if category_filter:
        docs = docs.filter(category=category_filter)

    categories = []
    for cat_key, cat_label in CATEGORY_CHOICES:
        count = member.documents.filter(category=cat_key).count()
        categories.append({
            'key': cat_key,
            'label': cat_label,
            'emoji': CATEGORY_META[cat_key]['emoji'],
            'count': count,
            'active': cat_key == category_filter,
        })

    return render(request, 'vault/member_detail.html', {
        'member': member,
        'docs': docs,
        'categories': categories,
        'category_filter': category_filter,
        'active_cat_meta': CATEGORY_META.get(category_filter) if category_filter else None,
    })


@login_required
def add_member(request):
    if request.method == 'POST':
        form = FamilyMemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.owner = request.user
            member.order = FamilyMember.objects.filter(owner=request.user).count()
            member.save()
            messages.success(request, f'{member.display_name} added to the vault!')
            return redirect('home')
    else:
        form = FamilyMemberForm()
    return render(request, 'vault/add_member.html', {'form': form})


# ── DOCUMENT ──────────────────────────────────────

@login_required
def document_viewer(request, pk):
    doc = get_object_or_404(Document, pk=pk, member__owner=request.user)
    return render(request, 'vault/document_viewer.html', {'doc': doc})


@login_required
def document_download(request, pk):
    doc = get_object_or_404(Document, pk=pk, member__owner=request.user)
    if not doc.drive_file_id:
        raise Http404("No file attached.")
    try:
        content, mime_type, filename = google_drive.download_file(doc.drive_file_id)
    except Exception as e:
        messages.error(request, f"Download failed: {e}")
        return redirect('document_viewer', pk=pk)
    response = HttpResponse(content, content_type=mime_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def document_convert(request, pk):
    """Download from Drive, convert format/size using Pillow, serve directly."""
    doc = get_object_or_404(Document, pk=pk, member__owner=request.user)
    if not doc.drive_file_id:
        messages.error(request, "No file to convert.")
        return redirect('document_viewer', pk=pk)

    if doc.file_type != 'image':
        messages.error(request, "Conversion is only supported for image files.")
        return redirect('document_viewer', pk=pk)

    target_format = request.POST.get('format', 'jpeg').lower()
    target_size_kb = int(request.POST.get('size_kb', 0) or 0)
    max_width = int(request.POST.get('max_width', 0) or 0)

    try:
        from PIL import Image
    except ImportError:
        messages.error(request, "Image conversion library not installed.")
        return redirect('document_viewer', pk=pk)

    try:
        content, _, _ = google_drive.download_file(doc.drive_file_id)
    except Exception as e:
        messages.error(request, f"Download failed: {e}")
        return redirect('document_viewer', pk=pk)

    try:
        img = Image.open(io.BytesIO(content))

        # Resize by max width
        if max_width and img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

        output = io.BytesIO()

        if target_format == 'png':
            img = img.convert('RGBA') if img.mode in ('P',) else img
            img.save(output, format='PNG', optimize=True)
            mime = 'image/png'
            ext = 'png'

        elif target_format == 'webp':
            if img.mode in ('P', 'RGBA'):
                img = img.convert('RGBA')
            quality = 85
            if target_size_kb:
                for q in range(90, 5, -5):
                    output = io.BytesIO()
                    img.save(output, format='WEBP', quality=q)
                    if len(output.getvalue()) / 1024 <= target_size_kb:
                        break
            else:
                img.save(output, format='WEBP', quality=quality)
            mime = 'image/webp'
            ext = 'webp'

        else:  # jpeg (default)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            if target_size_kb:
                for q in range(95, 5, -5):
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=q, optimize=True)
                    if len(output.getvalue()) / 1024 <= target_size_kb:
                        break
            else:
                img.save(output, format='JPEG', quality=85, optimize=True)
            mime = 'image/jpeg'
            ext = 'jpg'

        output.seek(0)
        safe_name = doc.name.replace(' ', '_')
        response = HttpResponse(output.read(), content_type=mime)
        response['Content-Disposition'] = f'attachment; filename="{safe_name}_converted.{ext}"'
        return response

    except Exception as e:
        messages.error(request, f"Conversion failed: {e}")
        return redirect('document_viewer', pk=pk)


@login_required
def document_rename(request, pk):
    doc = get_object_or_404(Document, pk=pk, member__owner=request.user)
    if request.method == 'POST':
        form = DocumentRenameForm(request.POST, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, 'Document updated.')
            return redirect('document_viewer', pk=doc.pk)
    else:
        form = DocumentRenameForm(instance=doc)
    return render(request, 'vault/document_rename.html', {'form': form, 'doc': doc})


@login_required
@require_POST
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk, member__owner=request.user)
    member_pk = doc.member.pk
    doc_name = doc.name
    if doc.drive_file_id:
        try:
            google_drive.delete_file(doc.drive_file_id)
        except Exception as e:
            messages.warning(request, f"Deleted locally but Drive removal failed: {e}")
    doc.delete()
    messages.success(request, f'"{doc_name}" deleted.')
    return redirect('member_detail', pk=member_pk)


# ── UPLOAD ────────────────────────────────────────

@login_required
def upload(request):
    members = FamilyMember.objects.filter(owner=request.user)
    initial_member = request.GET.get('member')

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            member = form.cleaned_data['member']
            category = form.cleaned_data['category']
            name = form.cleaned_data['name']
            file_type = form.cleaned_data['file_type']
            notes = form.cleaned_data['notes']
            uploaded_file = form.cleaned_data['file']
            try:
                file_id, view_url, file_size = google_drive.upload_file(
                    file_obj=uploaded_file,
                    filename=uploaded_file.name,
                    member_name=member.display_name,
                    category_name=CATEGORY_META[category]['label'],
                )
                doc = Document.objects.create(
                    member=member, category=category, name=name,
                    file_type=file_type, drive_file_id=file_id,
                    drive_view_url=view_url, file_size=file_size, notes=notes,
                )
                messages.success(request, f'"{name}" uploaded successfully!')
                return redirect('document_viewer', pk=doc.pk)
            except FileNotFoundError:
                messages.error(request, "Google Drive is not configured. Add token.json and set GOOGLE_DRIVE_FOLDER_ID.")
            except Exception as e:
                messages.error(request, f"Upload failed: {e}")
    else:
        initial = {}
        if initial_member:
            initial['member'] = initial_member
        form = DocumentUploadForm(initial=initial, user=request.user)

    return render(request, 'vault/upload.html', {
        'form': form,
        'members': members,
        'category_meta': CATEGORY_META,
    })
