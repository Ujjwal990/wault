from django.conf import settings


def family_context(request):
    return {
        'FAMILY_NAME': settings.FAMILY_NAME,
    }
