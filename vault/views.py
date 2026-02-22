import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.db.models import Q, Count
from django.views.decorators.http import require_POST

from .models import FamilyMember, Document, CATEGORY_CHOICES, CATEGORY_META
from .forms import DocumentUploadForm, FamilyMemberForm, DocumentRenameForm
from . import google_drive


@login_required
def home(request):
    members = FamilyMember.objects.annotate(doc_count_ann=Count('documents'))
    recent_docs = Document.objects.select_related('member').order_by('-updated_at')[:8]
    total_docs = Document.objects.count()

    query = request.GET.get('q', '').strip()
    search_results = None
    if query:
        search_results = Document.objects.select_related('member').filter(
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


@login_required
def member_detail(request, pk):
    member = get_object_or_404(FamilyMember, pk=pk)
    category_filter = request.GET.get('cat', '')

    docs = member.documents.all()
    if category_filter:
        docs = docs.filter(category=category_filter)

    # Build category summary
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
def document_viewer(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    return render(request, 'vault/document_viewer.html', {
        'doc': doc,
    })


@login_required
def document_download(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if not doc.drive_file_id:
        raise Http404("No file attached to this document.")
    try:
        content, mime_type, filename = google_drive.download_file(doc.drive_file_id)
    except Exception as e:
        messages.error(request, f"Download failed: {e}")
        return redirect('document_viewer', pk=pk)

    response = HttpResponse(content, content_type=mime_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def upload(request):
    members = FamilyMember.objects.all()
    # Pre-select member from query param
    initial_member = request.GET.get('member')

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
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
                    member=member,
                    category=category,
                    name=name,
                    file_type=file_type,
                    drive_file_id=file_id,
                    drive_view_url=view_url,
                    file_size=file_size,
                    notes=notes,
                )
                messages.success(request, f'"{name}" uploaded successfully to Google Drive!')
                return redirect('document_viewer', pk=doc.pk)

            except FileNotFoundError:
                messages.error(
                    request,
                    "Google Drive is not configured yet. Please add your service_account.json "
                    "and set GOOGLE_DRIVE_FOLDER_ID in your .env file."
                )
            except Exception as e:
                messages.error(request, f"Upload failed: {e}")
    else:
        initial = {}
        if initial_member:
            initial['member'] = initial_member
        form = DocumentUploadForm(initial=initial)

    return render(request, 'vault/upload.html', {
        'form': form,
        'members': members,
        'category_meta': CATEGORY_META,
    })


@login_required
def document_rename(request, pk):
    doc = get_object_or_404(Document, pk=pk)
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
    doc = get_object_or_404(Document, pk=pk)
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


@login_required
def add_member(request):
    if request.method == 'POST':
        form = FamilyMemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.order = FamilyMember.objects.count()
            member.save()
            messages.success(request, f'{member.display_name} added to the vault!')
            return redirect('home')
    else:
        form = FamilyMemberForm()
    return render(request, 'vault/add_member.html', {'form': form})
