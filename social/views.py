from django.shortcuts import render


from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from blog.models import BlogPost

from .models import BlogComment
from .services import (
    create_comment,
    create_report,
    edit_comment,
    toggle_bookmark,
    toggle_reaction,
)


def _messages(exc):
    return getattr(exc, "messages", [str(exc)])


def _wants_json(request):
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )


def _success_response(request, *, post=None, payload=None):
    payload = payload or {}
    if _wants_json(request):
        return JsonResponse(payload)
    if post is not None:
        return redirect(post.get_absolute_url())
    return JsonResponse(payload)


def _error_response(request, exc, *, status=400, post=None):
    payload = {"ok": False, "errors": _messages(exc)}
    if _wants_json(request) or post is None:
        return JsonResponse(payload, status=status)
    return redirect(post.get_absolute_url())


@login_required(login_url="login")
@require_POST
def comment_create(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id, status="published")
    parent = None
    parent_id = request.POST.get("parent_id")

    if parent_id:
        parent = get_object_or_404(
            BlogComment,
            pk=parent_id,
            post=post,
            status=BlogComment.Status.APPROVED,
        )

    try:
        comment = create_comment(
            post=post,
            user=request.user,
            content=request.POST.get("content", ""),
            parent=parent,
        )
    except (ValidationError, PermissionDenied) as exc:
        return _error_response(request, exc, post=post)

    return _success_response(
        request,
        post=post,
        payload={
            "ok": True,
            "created": True,
            "comment_id": comment.pk,
            "status": comment.status,
        },
    )


@login_required(login_url="login")
@require_POST
def comment_edit(request, comment_id):
    comment = get_object_or_404(BlogComment.objects.select_related("post"), pk=comment_id)

    try:
        comment = edit_comment(
            comment=comment,
            user=request.user,
            content=request.POST.get("content", ""),
        )
    except PermissionDenied as exc:
        return _error_response(request, exc, status=403, post=comment.post)
    except ValidationError as exc:
        return _error_response(request, exc, post=comment.post)

    return _success_response(
        request,
        post=comment.post,
        payload={"ok": True, "updated": True, "comment_id": comment.pk},
    )


@login_required(login_url="login")
@require_POST
def reaction_toggle(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id, status="published")

    try:
        state, reaction, count = toggle_reaction(
            post=post,
            user=request.user,
            reaction_type=request.POST.get("reaction_type", "like"),
        )
    except ValidationError as exc:
        return _error_response(request, exc, post=post)

    return _success_response(
        request,
        post=post,
        payload={
            "ok": True,
            "state": state,
            "reaction_type": reaction.reaction_type if reaction else None,
            "reaction_count": count,
        },
    )


@login_required(login_url="login")
@require_POST
def bookmark_toggle(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id, status="published")
    state, _, count = toggle_bookmark(post=post, user=request.user)

    return _success_response(
        request,
        post=post,
        payload={
            "ok": True,
            "state": state,
            "bookmark_count": count,
        },
    )


@login_required(login_url="login")
@require_POST
def report_content(request):
    post = None
    comment = None
    post_id = request.POST.get("post_id")
    comment_id = request.POST.get("comment_id")

    if post_id:
        post = get_object_or_404(BlogPost, pk=post_id, status="published")
    if comment_id:
        comment = get_object_or_404(
            BlogComment.objects.select_related("post"),
            pk=comment_id,
        )

    redirect_post = post or (comment.post if comment else None)

    try:
        report = create_report(
            reported_by=request.user,
            post=post,
            comment=comment,
            reason=request.POST.get("reason", ""),
            description=request.POST.get("description", ""),
        )
    except ValidationError as exc:
        return _error_response(request, exc, post=redirect_post)

    return _success_response(
        request,
        post=redirect_post,
        payload={"ok": True, "created": True, "report_id": report.pk},
    )
