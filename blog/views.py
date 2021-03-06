import re
from urllib import request as urllib

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.utils import timezone
from blog.models import Post, Comment, HashTag
from .forms import PostForm, CommentForm, SummerForm
from django.shortcuts import redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def about(request):
    return render(request, 'blog/about.html')


def post_list(request):
    posts_list = Post.objects.filter(published_date__lte=timezone.now()).order_by('-create_date')

    paginator = Paginator(posts_list, 5)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # 페이지가 정수가 아닌 경우 1페이지 출력
        posts = paginator.page(1)
    except EmptyPage:
        # 페이지 범위가 넘어가면 맨 마지막 페이지 출력
        posts = paginator.page(paginator.num_pages)

    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, published_date__lte=timezone.now())

    prev_post = Post.objects.filter(pk__lt=post.pk, published_date__lte=timezone.now()).order_by('-pk')
    next_post = Post.objects.filter(pk__gt=post.pk, published_date__lte=timezone.now()).order_by('pk')

    try:
        reffer = request.META.get('HTTP_REFERER')
        # 한글이 유니코드로 넘어와서 변경 시켜줘야함.
        reffer = urllib.unquote(reffer)
        hash_tag = re.search(r'(#[ㄱ-ㅎ가-힣a-zA-Z0-9]+)', reffer)[0]
    except TypeError:
        hash_tag = None

    return render(request, 'blog/post_detail.html',
                  {'post': post, 'prev_post': prev_post, 'next_post': next_post, 'hash_tag': hash_tag})


@login_required
def post_draft_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, published_date__isnull=True)
    prev_post = Post.objects.filter(pk__lt=post.pk, published_date__isnull=True).order_by('-pk')
    next_post = Post.objects.filter(pk__gt=post.pk, published_date__isnull=True).order_by('pk')

    return render(request, 'blog/post_draft_detail.html',
                  {'post': post, 'prev_post': prev_post, 'next_post': next_post})


@login_required
def post_new(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            hashtag = request.POST['hashtag']
            post.save_hash_tag_list(hashtag)

            return redirect('post_draft_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=pk)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_draft_list(request):
    posts_list = Post.objects.filter(published_date__isnull=True).order_by('-create_date')
    paginator = Paginator(posts_list, 5)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # 페이지가 정수가 아닌 경우 1페이지 출력
        posts = paginator.page(1)
    except EmptyPage:
        # 페이지 범위가 넘어가면 맨 마지막 페이지 출력
        posts = paginator.page(paginator.num_pages)

    return render(request, 'blog/post_draft_list.html', {'posts': posts})


@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return_url = post.publish()
    return redirect(return_url, pk=pk)


@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if post.published_date:
        redirect_url = 'post_list'
    else:
        redirect_url = 'post_draft_list'

    post.delete()
    return redirect(redirect_url)


def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment_to_post.html', {'form': form})


@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return redirect('post_detail', pk=comment.post.pk)


@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    return redirect('post_detail', pk=comment.post.pk)


def tags(request):
    hash_tag_list = HashTag.objects.filter(post__published_date__isnull=False).distinct()
    return render(request, 'blog/hash_tag_list.html', {'hash_tag_list': hash_tag_list})


def archive(request):
    posts_list = Post.objects.filter(published_date__lte=timezone.now()).order_by('-create_date')

    return render(request, 'blog/archive.html', {'': posts_list})
