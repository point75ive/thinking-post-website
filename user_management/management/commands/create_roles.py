# create_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from models import Role

class Command(BaseCommand):
    help = 'Creates roles and assigns permissions based on the proposed role hierarchy'

    def handle(self, *args, **options):
        # Define roles and their permissions
        roles_data = {
            # Academic Staff
            'HOD': {
                'permissions': ['add_department', 'change_department', 'delete_department', 'view_course', 'publish_course'],
                'category': 'academic',
                'is_supervisor': True,
                'subordinates': ['Lecturer', 'TA'],
            },
            'Lecturer': {
                'permissions': ['view_course', 'publish_course', 'enroll_students'],
                'category': 'academic',
                'is_supervisor': False,
                'subordinates': [],
            },
            'TA': {
                'permissions': ['view_course', 'enroll_students'],
                'category': 'academic',
                'is_supervisor': False,
                'subordinates': [],
            },

            # Administrative Staff
            'Registrar': {
                'permissions': ['manage_student_records', 'manage_course_registrations'],
                'category': 'admin',
                'is_supervisor': True,
                'subordinates': ['Clerk', 'Secretary'],
            },
            'Clerk': {
                'permissions': ['manage_student_records'],
                'category': 'admin',
                'is_supervisor': False,
                'subordinates': [],
            },
            'Secretary': {
                'permissions': ['manage_course_registrations'],
                'category': 'admin',
                'is_supervisor': False,
                'subordinates': [],
            },

            # Boarding Staff
            'Hostel Manager': {
                'permissions': ['manage_hostel_allocations', 'manage_hostel_fees'],
                'category': 'boarding',
                'is_supervisor': True,
                'subordinates': ['Warden', 'Caretaker'],
            },
            'Warden': {
                'permissions': ['manage_hostel_allocations'],
                'category': 'boarding',
                'is_supervisor': False,
                'subordinates': [],
            },
            'Caretaker': {
                'permissions': ['manage_hostel_fees'],
                'category': 'boarding',
                'is_supervisor': False,
                'subordinates': [],
            },

            # Security Staff
            'Chief Security Officer': {
                'permissions': ['manage_security_logs', 'manage_security_personnel'],
                'category': 'security',
                'is_supervisor': True,
                'subordinates': ['Guard', 'Patrol Officer'],
            },
            'Guard': {
                'permissions': ['manage_security_logs'],
                'category': 'security',
                'is_supervisor': False,
                'subordinates': [],
            },
            'Patrol Officer': {
                'permissions': ['manage_security_personnel'],
                'category': 'security',
                'is_supervisor': False,
                'subordinates': [],
            },

            # Accounting Staff
            'CFO': {
                'permissions': ['manage_budget', 'approve_payments'],
                'category': 'accounting',
                'is_supervisor': True,
                'subordinates': ['Accounts Manager', 'Accountant'],
            },
            'Accounts Manager': {
                'permissions': ['manage_budget'],
                'category': 'accounting',
                'is_supervisor': False,
                'subordinates': [],
            },
            'Accountant': {
                'permissions': ['approve_payments'],
                'category': 'accounting',
                'is_supervisor': False,
                'subordinates': [],
            },

            # Students
            'Class Rep': {
                'permissions': ['view_class_attendance', 'submit_feedback'],
                'category': 'student',
                'is_supervisor': True,
                'subordinates': ['Regular Student'],
            },
            'Regular Student': {
                'permissions': ['view_class_attendance'],
                'category': 'student',
                'is_supervisor': False,
                'subordinates': [],
            },
        }

        # Create roles and assign permissions
        for role_name, config in roles_data.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                category=config['category'],
                is_supervisor=config['is_supervisor'],
            )

            # Assign permissions
            for perm_codename in config['permissions']:
                try:
                    perm = Permission.objects.get(codename=perm_codename)
                    role.permissions.add(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Permission {perm_codename} does not exist. Skipping.'))

            # Assign subordinates (hierarchy)
            for subordinate_name in config['subordinates']:
                try:
                    subordinate_role = Role.objects.get(name=subordinate_name)
                    subordinate_role.parent = role
                    subordinate_role.save()
                except Role.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Subordinate role {subordinate_name} does not exist. Skipping.'))

            self.stdout.write(self.style.SUCCESS(f'Created/updated role: {role_name}'))

        self.stdout.write(self.style.SUCCESS('Role hierarchy created successfully!'))