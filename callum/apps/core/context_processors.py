from django.conf import settings


def callum_globals(request):
    return {
        "CALLUM_GATEWAY_CODE": settings.CALLUM_GATEWAY_CODE,
    }
