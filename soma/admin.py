from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import (
    EnrollmentStatus, Course, Session, Enrollment,
    Fee, Payment, Timetable,
    LearningMaterial, Recording, FeeStatus, PaymentStatus
)

@admin.register(EnrollmentStatus)
class EnrollmentStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_deleted')  # Added is_deleted
    list_filter = ('name', 'is_deleted')  # Added is_deleted
    ordering = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'instructor', 'start_date', 'end_date', 'fee', 'is_deleted')  # Added is_deleted
    list_filter = ('instructor', 'start_date', 'is_deleted')  # Added is_deleted
    search_fields = ('name', 'description')
    ordering = ('-start_date',)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'created_at', 'is_deleted')  # Added is_deleted
    list_filter = ('course', 'is_deleted')  # Added is_deleted
    search_fields = ('name',)
    ordering = ('course', 'name')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'session', 'enrollment_status', 'created_at', 'is_deleted')  # Added is_deleted
    list_filter = ('enrollment_status', 'course', 'session', 'is_deleted')  # Added is_deleted
    search_fields = ('user__username', 'course__name')
    raw_id_fields = ('user', 'course', 'session')
    ordering = ('-created_at',)

@admin.register(FeeStatus)
class FeeStatusAdmin(admin.ModelAdmin):  # Added FeeStatus Admin
    list_display = ('name', 'created_at', 'is_deleted')
    list_filter = ('name', 'is_deleted')
    ordering = ('name',)

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'amount', 'status', 'due_date', 'created_at', 'is_deleted')  # Added is_deleted
    list_filter = ('course', 'status', 'is_deleted')  # Added is_deleted
    search_fields = ('user__username', 'course__name')
    raw_id_fields = ('user', 'course')
    ordering = ('-due_date',)

@admin.register(PaymentStatus)
class PaymentStatusAdmin(admin.ModelAdmin):  # Added PaymentStatus Admin
    list_display = ('name', 'created_at', 'is_deleted')
    list_filter = ('name', 'is_deleted')
    ordering = ('name',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'amount', 'get_payment_status', 'created_at')
    list_filter = ('payment_status', 'course', 'created_at')
    actions = ['verify_payments']
    raw_id_fields = ('user', 'course')  # For better performance with ForeignKeys

    def get_user(self, obj):
        return obj.user.email  # or obj.user.get_full_name() or whatever identifier you prefer
    get_user.short_description = 'User'
    get_user.admin_order_field = 'user'

    def get_payment_status(self, obj):
        return obj.payment_status.name  # Assuming PaymentStatus has a 'name' field
    get_payment_status.short_description = 'Status'
    get_payment_status.admin_order_field = 'payment_status'

    def verify_payments(self, request, queryset):
        # Only process payments that are pending verification
        # Assuming you have a payment status named 'Pending'
        payments = queryset.filter(payment_status__name='Pending')
        count = 0
        
        for payment in payments:
            try:
                # Update payment status to 'Completed'
                completed_status = PaymentStatus.objects.get(name='Completed')
                payment.payment_status = completed_status
                payment.save()
                
                # Update enrollment status
                enrollment, created = Enrollment.objects.get_or_create(
                    user=payment.user,
                    course=payment.course,
                    defaults={'status': 'active'}
                )
                
                if not created:
                    enrollment.status = 'active'
                    enrollment.save()
                
                # Add any additional app logic here
                count += 1
                
            except Exception as e:
                self.message_user(
                    request,
                    f"Error processing payment {payment.id}: {str(e)}",
                    messages.ERROR
                )
        
        self.message_user(
            request,
            f"Successfully verified {count} payment(s).",
            messages.SUCCESS
        )
    
    verify_payments.short_description = "Verify selected payments"

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('course', 'session', 'day', 'time', 'location', 'session_link', 'is_deleted')  # Added is_deleted
    list_filter = ('course', 'day', 'is_deleted')  # Added is_deleted
    search_fields = ('course__name', 'location')
    raw_id_fields = ('course', 'session')
    ordering = ('day', 'time')

@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'created_at', 'is_deleted')  # Added is_deleted
    list_filter = ('course', 'is_deleted')  # Added is_deleted
    search_fields = ('name', 'description')
    raw_id_fields = ('course',)
    ordering = ('-created_at',)

@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'session', 'created_at', 'is_deleted')  # Added is_deleted
    list_filter = ('course', 'session', 'is_deleted')  # Added is_deleted
    search_fields = ('name', 'description')
    raw_id_fields = ('course', 'session')
    ordering = ('-created_at',)
