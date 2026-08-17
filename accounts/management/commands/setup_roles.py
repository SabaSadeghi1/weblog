from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db.models import Q


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        admin_group, created = Group.objects.get_or_create(
            name='Admin'
        )

        author_group, created = Group.objects.get_or_create(
            name='Author'
        )

        editor_group, created = Group.objects.get_or_create(
            name='Editor'
        )

        moderator_group, created = Group.objects.get_or_create(
            name='Moderator'
        )

        user_group, created = Group.objects.get_or_create(
            name='User'
        )



        admin_permissions = Permission.objects.filter(
            content_type__app_label__in=[
                'accounts',
                'core',
                'blog',
                'media',
                'social',
                'analytics',
                'discovery',
                'seo',
            ]
        )

        admin_group.permissions.set(
            admin_permissions
        )



        user_permissions = Permission.objects.filter(
            Q(
                content_type__app_label='social',
                codename__in=[
                    'add_blogcomment',
                    'view_blogcomment',
                    'add_blogreaction',
                    'view_blogreaction',
                    'add_blogbookmark',
                    'view_blogbookmark',
                    'add_blogcontentreport',
                    'view_blogcontentreport',
                ]
            )
        )

        user_group.permissions.set(
            user_permissions
        )



        author_permissions = Permission.objects.filter(

            Q(
                content_type__app_label='blog',
                codename__in=[
                    'add_blogpost',
                    'change_blogpost',
                    'view_blogpost',
                    'delete_blogpost',

                ]
            )

            |

            Q(
                content_type__app_label='media',
                codename__in=[
                    'add_mediaasset',
                    'view_mediaasset',
                ]
            )

        )

        author_group.permissions.set(
            author_permissions
        )



        editor_permissions = Permission.objects.filter(
            content_type__app_label='blog'
        )

        editor_group.permissions.set(
            editor_permissions
        )



        moderator_permissions = Permission.objects.filter(
            content_type__app_label='social',
            codename__in=[
                'view_blogcomment',
                'change_blogcomment',
                'view_blogcontentreport',
                'change_blogcontentreport',
            ]
        )

        moderator_group.permissions.set(
            moderator_permissions
        )


        self.stdout.write(
            self.style.SUCCESS(
                'Groups and permissions created.'
            )
        )