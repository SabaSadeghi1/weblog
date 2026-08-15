from .models import SiteSettings


def site_settings(request):

    settings_object = SiteSettings.objects.filter(
        singleton_key='global'
    ).first()

    return {
        'site_settings': settings_object
    }