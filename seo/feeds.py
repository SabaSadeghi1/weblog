from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils import timezone
from blog.models import BlogPost


class LatestPostsFeed(Feed):

    title = 'Comentic Latest Posts'

    link = '/posts/'

    description = 'Latest posts published on Comentic.'


    def items(self):

        return BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).order_by(
            '-published_at'
        )[:20]


    def item_title(self, item):

        return item.title


    def item_description(self, item):

        if item.summary:
            return item.summary

        return strip_tags(item.content)[:300]


    def item_link(self, item):

        return reverse(
            'blog:post_detail',
            kwargs={
                'slug': item.slug
            }
        )


    def item_pubdate(self, item):

        return item.published_at