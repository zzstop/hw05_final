from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Group, Post

User = get_user_model()


def page_not_found(request, exception):
    """Show page not found (404) error"""
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    """Show server error (500) error"""
    return render(request, 'misc/500.html', status=500)


def add_comment(request, post):
    """Add a new comment from an authorized user."""
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    form = CommentForm()
    return form


def index(request):
    """Collect 10 posts, sorted by time, on one page."""
    post_list = Post.objects.select_related('group')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'index.html', context)


def group_posts(request, slug):
    """Collect 10 posts, sorted by time, on one group page."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'group': group,
        'paginator': paginator,
    }
    return render(request, 'group.html', context)


@login_required
def new_post(request):
    """Add a new post from an authorized user."""
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    """Show all user posts on profile page."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'author': author,
        'paginator': paginator,
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    """Show one post info."""
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    comments = post.comments.all()
    form = add_comment(request, post)
    context = {
        'form': form,
        'post': post,
        'author': author,
        'comments': comments,
    }
    return render(request, 'post.html', context)


def post_edit(request, username, post_id):
    """Let change the post only to the author of the post"""
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    if author == request.user:
        form = PostForm(
            request.POST or None, files=request.FILES or None, instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post', username=username, post_id=post_id)
    else:
        return redirect('posts:post', username=author, post_id=post_id)
    context = {
        'post': post,
        'form': form,
    }
    return render(request, 'new_post.html', context)
