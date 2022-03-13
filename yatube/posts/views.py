from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from posts.models import Post, Group, User, Comment, Follow
from posts.forms import PostForm, CommentForm


COUNT_POST = 10


def getting_pages(post_list, request):
    paginator = Paginator(post_list, COUNT_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': getting_pages(post_list, request)
    }
    return render(request, 'posts/index.html', context)


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by('-pub_date')[:COUNT_POST]
    context = {
        'group': group,
        'page_obj': getting_pages(post_list, request)
    }
    return render(request, 'posts/group_list.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    form.pk = post_id
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/post_create.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post_id=post_id)
    form_comment = CommentForm(request.POST or None)
    context = {
        'post': post,
        'post_count': post.author.posts.count(),
        'comments': comments,
        'form_comment': form_comment

    }
    return render(request, 'posts/post_detail.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    if ((request.user.is_authenticated)
        and Follow.objects.filter(
            user=request.user, author=author).exists()):
        following = True
    else:
        following = False
    context = {
        'count': author.posts.count(),
        'author': author,
        'page_obj': getting_pages(post_list, request),
        'following': following
    }
    return render(request, 'posts/profile.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    author_ids = (Follow.objects.filter(user=request.user)
                  .values_list('author_id', flat=True))
    post_list = Post.objects.filter(author_id__in=author_ids)
    context = {
        'page_obj': getting_pages(post_list, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        if not Follow.objects.filter(
                user=request.user, author=author).exists():
            Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(
       user=request.user, author=author).exists():
        Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
