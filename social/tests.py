from django.test import TestCase

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import BlogCategory, BlogPost

from .models import BlogComment, BlogContentReport, BlogReaction
from .services import (
    create_comment,
    create_report,
    edit_comment,
    set_comment_status,
    toggle_bookmark,
    toggle_reaction,
)


class SocialTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="author",
            email="author@example.com",
            password="pass12345",
        )
        self.user = User.objects.create_user(
            username="reader",
            email="reader@example.com",
            password="pass12345",
        )
        self.other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="pass12345",
        )
        self.category = BlogCategory.objects.create(name="General")
        self.post = BlogPost.objects.create(
            author_user=self.author,
            category=self.category,
            title="Published post",
            summary="Summary",
            content="Content",
            status="published",
        )

    def test_create_comment_defaults_to_pending(self):
        comment = create_comment(post=self.post, user=self.user, content="Hello")
        self.assertEqual(comment.status, BlogComment.Status.PENDING)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 0)

    def test_comment_is_blocked_when_post_comments_are_closed(self):
        self.post.allow_comments = False
        self.post.save()
        with self.assertRaises(ValidationError):
            create_comment(post=self.post, user=self.user, content="Nope")

    def test_reply_must_belong_to_same_post(self):
        other_post = BlogPost.objects.create(
            author_user=self.author,
            category=self.category,
            title="Other post",
            summary="Summary",
            content="Content",
            status="published",
        )
        parent = create_comment(post=self.post, user=self.user, content="Parent")
        with self.assertRaises(ValidationError):
            create_comment(
                post=other_post,
                user=self.user,
                content="Wrong post reply",
                parent=parent,
            )

    def test_reply_depth_is_limited(self):
        root = create_comment(post=self.post, user=self.user, content="Root")
        reply = create_comment(post=self.post, user=self.other, content="Reply", parent=root)
        with self.assertRaises(ValidationError):
            create_comment(post=self.post, user=self.user, content="Too deep", parent=reply)

    def test_approving_comment_updates_only_approved_count(self):
        first = create_comment(post=self.post, user=self.user, content="One")
        create_comment(post=self.post, user=self.other, content="Two")
        set_comment_status(comment=first, status=BlogComment.Status.APPROVED)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)

    def test_comment_owner_can_edit_within_window(self):
        comment = create_comment(post=self.post, user=self.user, content="Before")
        edit_comment(comment=comment, user=self.user, content="After")
        comment.refresh_from_db()
        self.assertTrue(comment.is_edited)
        self.assertEqual(comment.content, "After")

    def test_comment_edit_rejects_non_owner(self):
        comment = create_comment(post=self.post, user=self.user, content="Before")
        with self.assertRaises(PermissionDenied):
            edit_comment(comment=comment, user=self.other, content="Hacked")

    def test_comment_edit_window_expires(self):
        comment = create_comment(post=self.post, user=self.user, content="Before")
        old_time = timezone.now() - timedelta(minutes=30)
        BlogComment.objects.filter(pk=comment.pk).update(created_at=old_time)
        comment.refresh_from_db()
        with self.assertRaises(PermissionDenied):
            edit_comment(comment=comment, user=self.user, content="Late edit")

    def test_reaction_toggle_create_update_remove_and_count(self):
        state, reaction, count = toggle_reaction(
            post=self.post,
            user=self.user,
            reaction_type=BlogReaction.ReactionType.LIKE,
        )
        self.assertEqual((state, count), ("created", 1))
        self.assertIsNotNone(reaction)

        state, reaction, count = toggle_reaction(
            post=self.post,
            user=self.user,
            reaction_type=BlogReaction.ReactionType.LOVE,
        )
        self.assertEqual((state, count), ("updated", 1))
        self.assertEqual(reaction.reaction_type, BlogReaction.ReactionType.LOVE)

        state, reaction, count = toggle_reaction(
            post=self.post,
            user=self.user,
            reaction_type=BlogReaction.ReactionType.LOVE,
        )
        self.assertEqual((state, count), ("removed", 0))
        self.assertIsNone(reaction)

    def test_bookmark_toggle_prevents_duplicates(self):
        state, _, count = toggle_bookmark(post=self.post, user=self.user)
        self.assertEqual((state, count), ("created", 1))
        state, _, count = toggle_bookmark(post=self.post, user=self.user)
        self.assertEqual((state, count), ("removed", 0))

    def test_report_requires_exactly_one_target(self):
        with self.assertRaises(ValidationError):
            create_report(
                reported_by=self.user,
                reason=BlogContentReport.Reason.SPAM,
            )

    def test_report_duplicate_target_is_rejected(self):
        create_report(
            reported_by=self.user,
            post=self.post,
            reason=BlogContentReport.Reason.SPAM,
        )
        with self.assertRaises(ValidationError):
            create_report(
                reported_by=self.user,
                post=self.post,
                reason=BlogContentReport.Reason.OTHER,
            )

    def test_report_can_target_comment(self):
        comment = create_comment(post=self.post, user=self.other, content="Bad content")
        report = create_report(
            reported_by=self.user,
            comment=comment,
            reason=BlogContentReport.Reason.HARASSMENT,
        )
        self.assertEqual(report.comment_id, comment.pk)
        self.assertIsNone(report.post_id)
    def test_report_rejects_both_targets_at_once(self):
        comment = create_comment(post=self.post, user=self.other, content="Target")
        with self.assertRaises(ValidationError):
            create_report(
                reported_by=self.user,
                post=self.post,
                comment=comment,
                reason=BlogContentReport.Reason.SPAM,
            )

    def test_moderator_permissions_allow_comment_and_report_admin_review(self):
        User = get_user_model()
        moderator = User.objects.create_user(
            username="moderator",
            email="moderator@example.com",
            password="pass12345",
            is_staff=True,
        )
        permissions = Permission.objects.filter(
            content_type__app_label="social",
            codename__in=[
                "view_blogcomment",
                "change_blogcomment",
                "view_blogcontentreport",
                "change_blogcontentreport",
            ],
        )
        moderator.user_permissions.add(*permissions)

        self.client.force_login(moderator)
        comment_response = self.client.get(
            reverse("admin:social_blogcomment_changelist")
        )
        report_response = self.client.get(
            reverse("admin:social_blogcontentreport_changelist")
        )
        self.assertEqual(comment_response.status_code, 200)
        self.assertEqual(report_response.status_code, 200)

