from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from learning.models import Department, Course, Lecturer
from user_management.models import CustomUser, Role, UserRole
class Command(BaseCommand):
    help = 'Creates HOD and Lecturer roles and assigns permissions'

    def handle(self, *args, **kwargs):
        # Create HOD Role
        hod_role, created = Role.objects.get_or_create(
            name='HOD',
            category='academic',
            is_supervisor=True,
        )
        self.stdout.write(self.style.SUCCESS('Created HOD role'))

        # Create Lecturer Role
        lecturer_role, created = Role.objects.get_or_create(
            name='Lecturer',
            category='academic',
            is_supervisor=False,
        )
        self.stdout.write(self.style.SUCCESS('Created Lecturer role'))

        # Assign Permissions to HOD Role
        content_type = ContentType.objects.get_for_model(Department)
        permissions = Permission.objects.filter(content_type=content_type)
        hod_role.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS('Assigned permissions to HOD role'))

        # Assign Permissions to Lecturer Role
        lecturer_role.permissions.add(
            Permission.objects.get(codename='view_department'),
            Permission.objects.get(codename='view_course'),
        )
        self.stdout.write(self.style.SUCCESS('Assigned permissions to Lecturer role'))

        # Create Test HOD User
        hod_user = CustomUser.objects.create_user(
            username='hod_user',
            email='hod@example.com',
            password='password123',
        )
        UserRole.objects.create(user=hod_user, role=hod_role, is_primary=True)
        self.stdout.write(self.style.SUCCESS('Created HOD user: hod_user'))

        # Create Test Lecturer User
        lecturer_user = CustomUser.objects.create_user(
            username='lecturer_user',
            email='lecturer@example.com',
            password='password123',
        )
        UserRole.objects.create(user=lecturer_user, role=lecturer_role, is_primary=True)
        self.stdout.write(self.style.SUCCESS('Created Lecturer user: lecturer_user'))

        # Create a Test Department
        department = Department.objects.create(name='Computer Science')
        self.stdout.write(self.style.SUCCESS('Created Department: Computer Science'))

        # Assign HOD to Department
        Lecturer.objects.create(
            user=hod_user,
            department=department,
            is_main_lecturer=True,
        )
        self.stdout.write(self.style.SUCCESS('Assigned HOD to Computer Science department'))

        # Assign Lecturer to Department
        Lecturer.objects.create(
            user=lecturer_user,
            department=department,
            is_main_lecturer=False,
        )
        self.stdout.write(self.style.SUCCESS('Assigned Lecturer to Computer Science department'))