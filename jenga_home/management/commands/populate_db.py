import os
import random
from datetime import datetime, timedelta
from django.core.files import File
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from faker import Faker
from django.db import models
from django.utils import timezone 
import requests
from taggit.models import Tag
from jenga_home.models import (
    BlogCategory, BlogPost, FeaturedLink, Comment,
    RequestType, FormRequest
)
from user_management.models import CustomUser, Role, UserRole
from soma.models import (
    EnrollmentStatus, Course, Session, Enrollment,
    Fee, Payment, Timetable, PaymentStatus, FeeStatus,
    LearningMaterial, Recording
)

fake = Faker()
User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with fake data for testing'

    def handle(self, *args, **options):
        self.stdout.write("Creating fake data...")
        
        # Create admin user
        admin = self.create_admin()
        
        # Create regular users
        users = self.create_users(10)
        
        # Create roles and assign to users
        self.create_roles_and_assign(users)
        
        # Populate jenga_home models
        self.populate_jenga_home(users)
        
        # Populate soma models
        self.populate_soma(users)
        
        self.stdout.write(self.style.SUCCESS("Successfully populated database with fake data!"))

    def create_admin(self):
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='jenga',
                email='giture@thinking-post.com',
                password='2Gingernuts*',
                first_name='Evans',
                last_name='Giture'
            )
            self.stdout.write(f"Created admin user: {admin.username}")
            return admin
        return User.objects.get(username='admin')

    def create_users(self, count):
        users = []
        for _ in range(count):
            try:
                username = fake.unique.user_name()
                email = fake.unique.email()
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'password': 'testpass123',
                        'first_name': fake.first_name(),
                        'last_name': fake.last_name()
                    }
                )
                if created:
                    users.append(user)
            except IntegrityError:
                continue
        
        self.stdout.write(f"Created {len(users)} regular users")
        return users

    def create_roles_and_assign(self, users):
        roles = []
        for role_name in ['Student', 'Instructor', 'Admin', 'Content Creator']:
            role, _ = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'category': 'academic' if role_name != 'Admin' else 'admin',
                    'is_supervisor': role_name in ['Instructor', 'Admin']
                }
            )
            roles.append(role)
        
        for user in users:
            UserRole.objects.create(
                user=user,
                role=random.choice(roles),
                is_primary=True
            )
        self.stdout.write(f"Created and assigned {len(roles)} roles")

    def populate_jenga_home(self, users):
        # Create blog categories
        categories = []
        for i in range(5):
            try:
                name = fake.unique.word().capitalize()
                category = BlogCategory.objects.create(
                    name=name,
                    slug=fake.unique.slug(),
                    order=i
                )
                categories.append(category)
            except Exception as e:
                self.stdout.write(f"Error creating category: {str(e)}")
                continue
        self.stdout.write(f"Created {len(categories)} blog categories")

        # Create blog posts
        posts = []
        for _ in range(20):
            try:
                status = random.choice(['draft', 'published', 'scheduled'])
                publish_date = fake.date_time_between(start_date='-1y', end_date='now')
                scheduled_date = fake.date_time_between(start_date='now', end_date='+1y') if status == 'scheduled' else None
                
                post = BlogPost.objects.create(
                    title=fake.sentence(nb_words=6),
                    slug=fake.unique.slug(),
                    excerpt=fake.sentence(nb_words=12),
                    content="\n".join(fake.paragraphs(nb=5)),
                    author=random.choice(users),
                    publish_date=publish_date if status in ['published', 'scheduled'] else None,
                    scheduled_date=scheduled_date,
                    status=status,
                    meta_title=fake.sentence(nb_words=4),
                    meta_description=fake.sentence(nb_words=8),
                )

                # Set categories (2-3 random categories per post)
                post.categories.set(random.sample(categories, k=random.randint(1, 3)))
                
                # Add tags (using TaggableManager)
                for _ in range(random.randint(2, 5)):
                    post.tags.add(fake.word())

                # Add featured image
                try:
                    image_url = "https://source.unsplash.com/random/1200x630"
                    response = requests.get(image_url, stream=True)
                    if response.status_code == 200:
                        temp_name = f"temp_{post.slug}.jpg"
                        with open(temp_name, 'wb') as f:
                            f.write(response.content)
                        with open(temp_name, 'rb') as f:
                            post.featured_image.save(f"featured_{post.slug}.jpg", File(f))
                        os.remove(temp_name)
                except Exception as e:
                    self.stdout.write(f"Error adding featured image to post {post.slug}: {str(e)}")

                # Add featured links (1-3 per post)
                for _ in range(random.randint(1, 3)):
                    FeaturedLink.objects.create(
                        blog_post=post,
                        title=fake.sentence(nb_words=3),
                        url=fake.url(),
                        order=random.randint(1, 5),
                        is_external=random.choice([True, False])
                    )

                posts.append(post)
            except Exception as e:
                self.stdout.write(f"Error creating post: {str(e)}")
                continue

        self.stdout.write(f"Created {len(posts)} blog posts")

        # Create comments for posts
        if posts:
            try:
                for post in random.sample(posts, k=min(10, len(posts))):
                    for _ in range(random.randint(1, 5)):
                        user = random.choice(users + [None])
                        Comment.objects.create(
                            blog_post=post,
                            user=user,
                            name=fake.name() if user is None else None,
                            email=fake.email() if user is None else None,
                            phone=fake.phone_number() if random.choice([True, False]) else None,
                            content=fake.paragraph(),
                            is_public=random.choice([True, False]),
                            is_approved=random.choice([True, False])
                        )
                self.stdout.write(f"Created comments for {min(10, len(posts))} posts")
            except Exception as e:
                self.stdout.write(f"Error creating comments: {str(e)}")
        else:
            self.stdout.write("No posts created, skipping comments")

        # Create request types
        request_types = []
        for name in ['Technical Support', 'Account Help', 'Content Request', 'Partnership']:
            try:
                rt = RequestType.objects.create(
                    name=name,
                    description=fake.paragraph(),
                    order=random.randint(1, 10)
                )
                request_types.append(rt)
            except Exception as e:
                self.stdout.write(f"Error creating request type {name}: {str(e)}")

        # Create form requests
        for _ in range(15):
            try:
                FormRequest.objects.create(
                    request_type=random.choice(request_types),
                    user=random.choice(users + [None]),
                    name=fake.name(),
                    email=fake.email(),
                    phone=fake.phone_number(),
                    company=fake.company(),
                    message="\n".join(fake.paragraphs(nb=3)),
                    status=random.choice(['new', 'in_progress', 'resolved'])
                )
            except Exception as e:
                self.stdout.write(f"Error creating form request: {str(e)}")

        self.stdout.write("Successfully populated jenga_home models")
    

    def populate_soma(self, users):
        # Create enrollment statuses
        statuses = []
        for name in ['Pending', 'Active', 'Inactive']:
            status = EnrollmentStatus.objects.create(name=name)
            statuses.append(status)
        
        # Create fee statuses
        fee_statuses = []
        for name in ['Pending', 'Paid', 'Overdue', 'Partially Paid']:
            status = FeeStatus.objects.create(name=name)
            fee_statuses.append(status)
        
        # Create payment statuses
        payment_statuses = []
        for name in ['Pending', 'Completed', 'Failed', 'Refunded']:
            status = PaymentStatus.objects.create(name=name)
            payment_statuses.append(status)
        
        # Create courses
        courses = []
        for i in range(5):
            try:
                course = Course.objects.create(
                    name=f"Course {i+1}: {fake.word().capitalize()}",
                    description=fake.paragraph(),
                    instructor=fake.name(),
                    start_date=fake.date_between(start_date='-1y', end_date='today'),
                    end_date=fake.date_between(start_date='today', end_date='+1y'),
                    fee=random.randint(100, 1000)
                )
                courses.append(course)
            except Exception as e:
                self.stdout.write(f"Error creating course: {str(e)}")
                continue
        
        # Create sessions for each course
        sessions = []
        for course in courses:
            for i in range(random.randint(3, 6)):
                session = Session.objects.create(
                    name=f"Session {i+1}",
                    course=course
                )
                sessions.append(session)
        
        # Create enrollments
        for user in random.sample(users, k=8):
            for course in random.sample(courses, k=random.randint(1, 3)):
                Enrollment.objects.create(
                    user=user,
                    course=course,
                    session=random.choice([s for s in sessions if s.course == course]),
                    enrollment_status=random.choice(statuses),
                    comments=fake.sentence() if random.choice([True, False]) else None
                )
        
        # Create fees and payments
        for enrollment in Enrollment.objects.all():
            fee = Fee.objects.create(
                user=enrollment.user,
                course=enrollment.course,
                amount=enrollment.course.fee,
                status=random.choice(fee_statuses),
                due_date=fake.date_time_between(start_date='-30d', end_date='+30d')
            )
            
            if fee.status.name == 'Paid':
                Payment.objects.create(
                    payment_status=random.choice([s for s in payment_statuses if s.name in ['Completed', 'Refunded']]),
                    phone_no=fake.phone_number(),
                    amount=fee.amount,
                    mpesa_ref=fake.uuid4()[:20],
                    user=enrollment.user,
                    course=enrollment.course
                )
        
        # Create timetables
        for session in sessions:
            Timetable.objects.create(
                course=session.course,
                session=session,
                day=random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
                time=f"{random.randint(8, 16)}:00",
                location=fake.city(),
                session_link=fake.url() if random.choice([True, False]) else None
            )
        
        # Create learning materials
        for course in courses:
            for i in range(random.randint(2, 5)):
                LearningMaterial.objects.create(
                    name=f"Material {i+1} for {course.name}",
                    course=course,
                    description=fake.paragraph(),
                    document_link=fake.url() if random.choice([True, False]) else None
                )
        
        # Create recordings
        for session in sessions:
            Recording.objects.create(
                name=f"Recording for {session.name}",
                course=session.course,
                session=session,
                recording_link=fake.url(),
                recording_passcode=fake.password(length=8) if random.choice([True, False]) else None,
                description=fake.sentence() if random.choice([True, False]) else None
            )
        
        self.stdout.write("Successfully populated soma models")