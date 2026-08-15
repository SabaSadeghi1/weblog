from django.http import HttpResponse


def robots_txt(request):

    sitemap_url = request.build_absolute_uri(
        "/sitemap.xml"
    )

    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /register/",
        f"Sitemap: {sitemap_url}",
    ]

    return HttpResponse(
        "\n".join(lines),
        content_type="text/plain"
    )