from django.db import models
from django.core.exceptions import ValidationError


class EnrollmentStatus(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'enrollment_status'
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__in=['Pending', 'Active', 'Inactive']),
                name='enrollment_status'
            )
        ]

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    instructor = models.CharField(max_length=100)
    start_date = models.DateField()  # Changed to DateField
    end_date = models.DateField()  # Changed to DateField
    fee = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'course'

    def __str__(self):
        return self.name


class Session(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'session'
        unique_together = ('name', 'course')  # Added unique constraint

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    user = models.ForeignKey("user_management.CustomUser", on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    enrollment_status = models.ForeignKey(EnrollmentStatus, on_delete=models.CASCADE, related_name='enrollments')
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'enrollment'

    def __str__(self):
        return f"Enrollment {self.id}"


class FeeStatus(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'fee_status'
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__in=['Pending', 'Paid', 'Overdue', 'Partially Paid']),
                name='fee_status'
            )
        ]

    def __str__(self):
        return self.name


class Fee(models.Model):
    user = models.ForeignKey("user_management.CustomUser", on_delete=models.CASCADE, related_name='fees')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='fees')
    amount = models.FloatField()
    status = models.ForeignKey(FeeStatus, on_delete=models.CASCADE, related_name='fees')  # Changed to ForeignKey
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'fee'

    def __str__(self):
        return f"Fee {self.id}"


class PaymentStatus(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'payment_status'
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__in=['Pending', 'Completed', 'Failed', 'Refunded']),
                name='payment_status'
            )
        ]

    def __str__(self):
        return self.name


class Payment(models.Model):
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE,
                                     related_name='payments')  # Renamed and changed to ForeignKey
    phone_no = models.CharField(max_length=20)
    amount = models.FloatField()  # Changed to FloatField
    mpesa_ref = models.CharField(max_length=20)
    user = models.ForeignKey("user_management.CustomUser", on_delete=models.CASCADE,
                             related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'payment'

    def __str__(self):
        return f"Payment {self.id}"


class Timetable(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='timetables')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetables')
    day = models.CharField(max_length=3, choices=[
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    ])
    time = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    session_link = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'timetable'

    def __str__(self):
        return f"Timetable {self.id}"


class LearningMaterial(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learning_materials')
    description = models.TextField(null=True, blank=True)
    document_link = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'learning_material'

    def __str__(self):
        return self.name


class Recording(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='recordings')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='recordings')
    recording_link = models.CharField(max_length=255, null=True, blank=True)
    recording_passcode = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'recording'

    def __str__(self):
        return self.name