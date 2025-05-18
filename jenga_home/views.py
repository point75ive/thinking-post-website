from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from .models import BlogPost, BlogCategory, Comment, RequestType, FormRequest
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from taggit.models import Tag  # Changed import for tags
from django.core.exceptions import ValidationError
from django.views.generic.base import TemplateView


# Create your views here.
class RobotsTxtView(TemplateView):
    template_name = "robots.txt"
    content_type = "text/plain"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["SITE_URL"] = settings.SITE_URL
        return context

def home(request):
    return render(request, "home/home.html")


def services(request):
    return render(request, "home/services.html")


def bda(request):
    return render(request, "home/bda.html")




def about(request):
    return render(request, "home/about.html")



def contact_page(request):
    # Create default request types if they don't exist
    default_request_types = [
        "Demo Request",
        "Training Inquiry", 
        "Partnership",
        "Other"
    ]
    
    for req_type in default_request_types:
        RequestType.objects.get_or_create(name=req_type)
    
    if request.method == 'POST':
        try:
            # Get or create the request type
            request_type, created = RequestType.objects.get_or_create(
                name=request.POST.get('request_type', 'Other')
            )
            
            # Create the form request
            form_request = FormRequest.objects.create(
                request_type=request_type,
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                company=request.POST.get('company'),
                message=request.POST.get('message'),
                status='new'
            )
            
            # Add referral source to message if provided
            referral_source = request.POST.get('referral_source')
            if referral_source:
                form_request.message = f"How they heard about us: {referral_source}\n\n{form_request.message}"
                form_request.save()
            
            # Send email notification
            send_mail(
                subject=f"New Contact Request: {request_type.name}",
                message=f"""
                New contact request from {form_request.name} ({form_request.email})
                
                Request Type: {request_type.name}
                Company: {form_request.company or 'Not provided'}
                Phone: {form_request.phone or 'Not provided'}
                
                Message:
                {form_request.message}
                
                ---
                Thinking Post Training
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            
            # Send confirmation to user
            if form_request.email:
                send_mail(
                    subject="Thank you for contacting Thinking Post Training",
                    message=f"""
                    Dear {form_request.name},
                    
                    Thank you for reaching out to us. We have received your {request_type.name.lower()} 
                    and our team will get back to you within 24-48 hours.
                    
                    Your request details:
                    Request Type: {request_type.name}
                    Message: {form_request.message[:200]}...
                    
                    If you have any urgent questions, please call us at +254 724 501 565.
                    
                    Best regards,
                    Thinking Post Training Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[form_request.email],
                    fail_silently=True,
                )
            
            messages.success(request, "Thank you for your message! We'll get back to you soon.")
            return redirect('contact_success')
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Contact form error: {str(e)}")
    
    # Get all request types for the dropdown
    request_types = RequestType.objects.all().order_by('name')
    
    return render(request, 'home/contact_page.html', {
        'request_types': request_types,
    })

def contact_success(request):
    return render(request, 'home/contact_success.html')


@require_GET
def index(request):
    category_slug = request.GET.get('category')
    posts = BlogPost.objects.filter(status='published')
    if category_slug:
        category = get_object_or_404(BlogCategory, slug=category_slug)
        posts = posts.filter(categories=category)
    paginator = Paginator(posts.order_by('-publish_date'), 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'blog/index.html', context)

@require_GET
def post_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    comments = post.comments.filter(is_approved=True).order_by('-created_at')
    
    # Pagination for comments
    comment_paginator = Paginator(comments, 10)
    comment_page = request.GET.get('comment_page')
    comment_page_obj = comment_paginator.get_page(comment_page)

    context = {
        'post': post,
        'comment_page_obj': comment_page_obj,
        'meta_title': post.get_meta_title(),
        'meta_description': post.get_meta_description(),
    }
    return render(request, 'blog/post_detail.html', context)

@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    
    # Handle comment submission
    try:
        comment = Comment(
            blog_post=post,
            user=request.user if request.user.is_authenticated else None,
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            content=request.POST.get('content'),
        )
        comment.full_clean()
        comment.save()
        messages.success(request, "Comment submitted for approval")
    except ValidationError as e:
        messages.error(request, f"Error: {', '.join(e.messages)}")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect(post.get_absolute_url())

def tag_view(request, slug):
    tag = get_object_or_404(Tag, slug=slug)  # Use taggit's Tag model
    tagged_posts = BlogPost.objects.filter(tags=tag, status='published').order_by('-publish_date')
    
    context = {
        'tag': tag,
        'tagged_posts': tagged_posts,
    }
    return render(request, 'blog/tags.html', context)

@require_POST
def like_post(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Please <a href="/accounts/login/">login</a> to like posts'
        }, status=403)
    
    post = get_object_or_404(BlogPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    # Return HTML snippet for the button
    return render(request, 'blog/_like_button.html', {
        'post': post,
        'liked': liked
    })

def handler404(request, exception):
    recent_posts = BlogPost.objects.filter(status='published').order_by('-publish_date')[:3]
    return render(request, '404.html', {'recent_posts': recent_posts}, status=404)

def author_posts(request, username):
    author = get_object_or_404(get_user_model(), username=username)
    posts = BlogPost.objects.filter(author=author, status='published').order_by('-publish_date')
    return render(request, 'blog/author.html', {'author': author, 'posts': posts})