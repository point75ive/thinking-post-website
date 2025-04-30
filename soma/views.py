import io
import logging
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib import messages
from django.http import HttpResponse, FileResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.urls import reverse
from django.db import transaction
from django.db.models import Sum
from reportlab.lib import colors
from reportlab.lib.pagesizes import inch, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from .models import (
    Course, Enrollment, EnrollmentStatus, Fee,
     Payment, Timetable, LearningMaterial, Recording, Session, FeeStatus, PaymentStatus
)
from .forms import EnrolForm, InvoiceForm, PaymentForm


logger = logging.getLogger(__name__)


@login_required
def student_home(request):
    user = request.user
    context = {"user": user}
    
    try:
        with transaction.atomic():
            # Get status objects safely
            pending_fee_status = FeeStatus.objects.filter(name="Pending", is_deleted=False).first()
            overdue_fee_status = FeeStatus.objects.filter(name="Overdue", is_deleted=False).first()
            partially_paid_status = FeeStatus.objects.filter(name="Partially Paid", is_deleted=False).first()
            completed_payment_status = PaymentStatus.objects.filter(name="Completed", is_deleted=False).first()

            if not all([pending_fee_status, overdue_fee_status, partially_paid_status, completed_payment_status]):
                raise ObjectDoesNotExist("One or more status records not found")

            # Get all enrollments with related data
            enrollments = Enrollment.objects.filter(
                user=user, 
                is_deleted=False
            ).select_related('course').prefetch_related(
                'course__fees',
                'course__payments'
            )

            courses = []
            pending_payments = []

            for enrollment in enrollments:
                course = enrollment.course
                
                # Calculate total paid amount
                total_paid = Payment.objects.filter(
                    user=user,
                    course=course,
                    payment_status=completed_payment_status,
                    is_deleted=False
                ).aggregate(Sum('amount'))['amount__sum'] or 0

                # Get the most recent fee for this course
                course_fee = Fee.objects.filter(
                    course=course,
                    user=user,
                    is_deleted=False
                ).order_by('-created_at').first()

                if course_fee:
                    # Calculate remaining balance
                    remaining_balance = course_fee.amount - total_paid
                    
                    # Add to pending payments if not fully paid
                    if remaining_balance > 0:
                        pending_payments.append({
                            "course": course,
                            "amount": remaining_balance,
                            "original_amount": course_fee.amount,
                            "paid_amount": total_paid,
                            "enrollment_id": enrollment.id,
                            "due_date": course_fee.due_date.strftime("%Y-%m-%d"),
                            "is_partial": total_paid > 0
                        })

                # Prepare course data for display
                courses.append({
                    "course": {
                        "name": course.name,
                        "description": course.description,
                        "instructor": course.instructor,
                        "start_date": course.start_date.strftime("%Y-%m-%d"),
                        "end_date": course.end_date.strftime("%Y-%m-%d"),
                        "fee": course.fee
                    },
                    "enrollment_status": enrollment.enrollment_status.name,
                    "enrollment_id": enrollment.id,
                    "is_paid": total_paid >= course.fee if course_fee else False,
                    "remaining_balance": remaining_balance if course_fee else 0,
                    "total_paid": total_paid
                })

            context["courses"] = courses
            context["pending_payments"] = pending_payments

    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        messages.error(request, "An error occurred while retrieving data. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messages.error(request, "An unexpected error occurred. Please try again.")

    return render(request, "soma/home.html", context)

@login_required
def register_payments(request):
    user = request.user
    context = {"user": user}  # Initialize context
    try:
        with transaction.atomic():
            pending_fee_status = FeeStatus.objects.get(name="Pending", is_deleted=False)
            pending_payment_status = PaymentStatus.objects.get(name="Pending", is_deleted=False)
            pending_fees = Fee.objects.filter(user=user, status=pending_fee_status, is_deleted=False)

            if request.method == "POST":
                form = PaymentForm(request.POST)
                if form.is_valid():
                    selected_fee_id = form.cleaned_data['fee_id']
                    fee = get_object_or_404(Fee, id=selected_fee_id, user=user, is_deleted=False)

                    try:
                        # Create a Payment record with "Pending" status
                        payment = Payment.objects.create(
                            user=user,
                            course=fee.course,
                            amount=fee.amount,  # Or get amount from form if different
                            payment_status=pending_payment_status,
                            phone_no="",  # You might get this from the user's profile or form
                            mpesa_ref="Awaiting Verification",  # Initial status
                            is_deleted=False
                        )

                        messages.success(request, "Payment initiated. Awaiting verification.")
                        return redirect('soma:student_home')  # Redirect to home or a confirmation page

                    except Exception as e:
                        logger.error(f"Error creating payment: {e}")
                        messages.error(request, "Error initiating payment. Please try again.")

            else:
                form = PaymentForm()

            context["form"] = form
            context["pending_fees"] = pending_fees

    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        context["error_message"] = "Fee not found. Please contact support."
    except MultipleObjectsReturned as e:
        logger.error(f"MultipleObjectsReturned: {e}")
        context["error_message"] = "Multiple fees found. Please contact support."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        context["error_message"] = "An unexpected error occurred. Please try again."

    return render(request, "soma/register_payments.html", context)


@login_required
def fees(request):
    user = request.user
    context = {"user": user}  # Initialize context
    try:
        fees = Fee.objects.filter(user=user, is_deleted=False)
        payments = Payment.objects.filter(user=user, is_deleted=False)

        fee_details = []
        total_fees = 0
        total_payments = 0

        for fee in fees:
            fee_details.append({
                "description": f"Fee for {fee.course.name}",
                "amount": -fee.amount,
                "date": fee.created_at.date(),
            })
            total_fees -= fee.amount

        for payment in payments:
            fee_details.append({
                "description": "Payment",
                "amount": payment.amount,
                "date": payment.created_at.date(),
                "id": payment.id,
            })
            total_payments += payment.amount

        fee_balance = total_fees + total_payments

        context["fee_details"] = fee_details
        context["fee_balance"] = fee_balance

    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        context["error_message"] = "Could not retrieve fee or payment details."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        context["error_message"] = "An unexpected error occurred while retrieving fee information."

    return render(request, "soma/fees.html", context)


@login_required
def timetable(request):
    user = request.user
    context = {"user": user}  # Initialize context
    try:
        active_enrollment_status = get_object_or_404(EnrollmentStatus, name="Active", is_deleted=False)
        active_enrollments = Enrollment.objects.filter(
            user=user, 
            enrollment_status=active_enrollment_status, 
            is_deleted=False
        )

        if not active_enrollments.exists():
            messages.warning(request, "You need an active enrollment to view the timetable.")
            return redirect(reverse('soma:student_home'))

        session_ids = [enrollment.session_id for enrollment in active_enrollments if enrollment.session_id]
        timetable_entries = Timetable.objects.filter(
            session_id__in=session_ids, 
            is_deleted=False
        ) if session_ids else []

        context["timetables"] = timetable_entries

    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        messages.error(request, "Could not retrieve timetable information.")
        return redirect(reverse('soma:student_home'))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messages.error(request, "An unexpected error occurred while retrieving timetable information.")
        return redirect(reverse('soma:student_home'))

    return render(request, "soma/timetable.html", context)

def get_sessions(request):
  course_id = request.GET.get('course')
  sessions = Session.objects.filter(course_id=course_id, is_deleted=False)
  return render(request, 'soma/session_options.html', {'sessions': sessions})

def partial_payment_amount_input(request):
    course_id = request.GET.get('course')
    if course_id:
        course = Course.objects.get(pk=course_id)
        min_payment = course.fee / 2
        return render(
            request,
            'soma/partial_payment_amount_input.html',
            {'min_payment': min_payment}
        )
    else:
        return render(
            request,
            'soma/partial_payment_amount_input.html',
            {'min_payment': 0}
        )

@require_GET
def get_course_fee(request):
    course_id = request.GET.get('course_id')
    try:
        course = Course.objects.get(id=course_id, is_deleted=False)
        return JsonResponse({
            'success': True,
            'fee': course.fee,
            'min_partial': (course.fee / 2),
            'half_fee': course.fee / 2,
            'formatted_fee': f"Ksh {course.fee:,.2f}",
            'formatted_min': f"Ksh {(course.fee / 2):,.2f}"
        })
    except (ValueError, Course.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Invalid course'}, status=400)

@login_required
def enrol(request):
    user = request.user
    context = {"user": user}
    
    try:
        form = EnrolForm(request.POST or None)
        context["form"] = form
        
        # Handle AJAX fee requests
        if request.method == 'GET' and 'course_id' in request.GET:
            try:
                course_id = request.GET.get('course_id')
                course = Course.objects.get(id=course_id, is_deleted=False)
                return JsonResponse({
                    'fee': course.fee,
                    'min_partial': (course.fee / 2) + 1000,
                    'half_fee': course.fee / 2
                })
            except (ValueError, Course.DoesNotExist):
                return JsonResponse({'error': 'Invalid course'}, status=400)
        
        if request.method == "POST":
            if form.is_valid():
                with transaction.atomic():
                    course = form.cleaned_data['course']
                    class_session = form.cleaned_data.get('session')
                    payment_option = form.cleaned_data['payment_option']
                    phone_no = form.cleaned_data['phone_no']
                    comments = form.cleaned_data.get('comments', '')
                    partial_payment_amount = form.cleaned_data.get('partial_payment_amount')

                    # Handle session selection
                    if not class_session:
                        class_session = Session.objects.filter(
                            course=course,
                            is_deleted=False
                        ).first()
                        if not class_session:
                            messages.error(request, "No available sessions for this course")
                            return render(request, "soma/enrol.html", context)

                    # Calculate fees
                    total_fee = course.fee
                    if payment_option == "half":
                        fee_charged = total_fee + 1000
                        min_payment = (total_fee / 2) + 1000
                        if not partial_payment_amount or partial_payment_amount < (total_fee / 2):
                            form.add_error(
                                'partial_payment_amount',
                                f"Partial payment must be at least Ksh {total_fee / 2:.2f}"
                            )
                            context['course_fee'] = total_fee
                            return render(request, "soma/enrol.html", context)
                        amount_due = float(partial_payment_amount)
                    else:
                        fee_charged = total_fee
                        amount_due = total_fee

                    # Get status objects
                    pending_enrollment_status = EnrollmentStatus.objects.get(
                        name="Pending", 
                        is_deleted=False
                    )
                    pending_fee_status = FeeStatus.objects.get(
                        name="Pending",
                        is_deleted=False
                    )
                    pending_payment_status = PaymentStatus.objects.get(
                        name="Pending", 
                        is_deleted=False
                    )

                    # Create records
                    enrollment = Enrollment.objects.create(
                        user=user,
                        course=course,
                        session=class_session,
                        enrollment_status=pending_enrollment_status,
                        comments=comments,
                        is_deleted=False
                    )

                    Fee.objects.create(
                        user=user,
                        course=course,
                        amount=fee_charged,
                        status=pending_fee_status,
                        due_date=timezone.now() + timedelta(days=30),
                        is_deleted=False
                    )

                    Payment.objects.create(
                        payment_status=pending_payment_status,
                        phone_no=phone_no,
                        amount=amount_due,
                        mpesa_ref="Awaiting Verification",
                        user=user,
                        course=course,
                        is_deleted=False
                    )

                    messages.success(
                        request, 
                        "Enrollment successful. Your payment is awaiting verification."
                    )
                    return redirect('soma:invoice', enrollment_id=enrollment.id)

    except Exception as e:
        logger.error(f"Error in enrol view: {e}")
        messages.error(request, "An unexpected error occurred during enrollment.")

    return render(request, "soma/enrol.html", context)


@login_required
def invoice(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, is_deleted=False)
    user = request.user
    course = enrollment.course
    
    try:
        with transaction.atomic():
            # Get the most recent fee and payment
            fee = Fee.objects.filter(
                user=user,
                course=course,
                is_deleted=False
            ).order_by('-created_at').first()
            
            completed_payment_status = PaymentStatus.objects.filter(name="Completed", is_deleted=False).first()
            
            total_paid = Payment.objects.filter(
                user=user,
                course=course,
                payment_status=completed_payment_status,
                is_deleted=False
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            remaining_amount = fee.amount - total_paid if fee else course.fee

            if request.method == "POST":
                form = InvoiceForm(request.POST)
                if form.is_valid():
                    mpesa_ref = form.cleaned_data['mpesa_ref']
                    payment_amount = form.cleaned_data.get('payment_amount', remaining_amount)
                    
                    if not mpesa_ref:
                        messages.error(request, "Mpesa reference is required")
                        return redirect(reverse('soma:invoice', kwargs={'enrollment_id': enrollment.id}))
                    
                    if payment_amount <= 0:
                        messages.error(request, "Payment amount must be positive")
                        return redirect(reverse('soma:invoice', kwargs={'enrollment_id': enrollment.id}))
                    
                    # Create new payment record
                    pending_status = PaymentStatus.objects.filter(name="Pending", is_deleted=False).first()
                    Payment.objects.create(
                        user=user,
                        course=course,
                        amount=payment_amount,
                        payment_status=pending_status,
                        mpesa_ref=mpesa_ref,
                        is_deleted=False
                    )
                    
                    messages.success(request, "Payment submitted for verification")
                    return redirect('soma:student_home')
            
            else:
                # Initialize form with remaining amount as default
                form = InvoiceForm(initial={
                    'payment_amount': remaining_amount
                })

            context = {
                "enrollment": enrollment,
                "user": user,
                "course": course,
                "form": form,
                "remaining_amount": remaining_amount,
                "total_paid": total_paid,
                "original_amount": fee.amount if fee else course.fee
            }
            
    except Exception as e:
        logger.error(f"Error in invoice view: {e}")
        messages.error(request, "An error occurred while processing your payment")
        return redirect('soma:student_home')
    
    return render(request, "soma/invoice.html", context)








@login_required
def receipt(request, payment_id):
    user = request.user
    context = {"user": user}  # Initialize context
    
    try:
        payment = get_object_or_404(Payment, id=payment_id, is_deleted=False)
        
        context["payment"] = payment
        context["user"] = payment.user
        context["course"] = payment.course
        
    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        messages.error(request, "Payment not found.")
        return redirect(reverse('soma:fees'))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messages.error(request, "An unexpected error occurred while retrieving receipt.")
        return redirect(reverse('soma:fees'))
    
    return render(request, "soma/receipt.html", context)


@login_required
def download_receipt(request, payment_id):
    user = request.user
    try:
        payment = get_object_or_404(Payment, id=payment_id, is_deleted=False)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        logo = "static/images/logo.png"

        # Header with logo
        header = [
            [
                canvas.Canvas(logo),
                Paragraph("<strong>Official Receipt</strong>", styles["Title"]),
            ]
        ]
        header_table = Table(header, colWidths=[1.5 * inch, 3.5 * inch])
        header_table.setStyle(
            TableStyle(
                [("ALIGN", (0, 0), (1, 0), "CENTER"), 
                 ("VALIGN", (0, 0), (1, 0), "MIDDLE")]
            )
        )
        elements.append(header_table)

        # Receipt details
        details = [
            ["Receipt Number", payment.id],
            ["Amount", payment.amount],
            ["Phone Number", payment.phone_no],
            ["M-Pesa Ref", payment.mpesa_ref],
            ["Payment Date", payment.created_at.date()],
            ["Username", payment.user.username],
            ["Course", payment.course.name],
        ]
        details_table = Table(details, colWidths=[1.5 * inch, 3.5 * inch])
        details_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(details_table)

        # Thank you note
        thank_you = Paragraph(
            "Thank you for your payment! If you have any questions, please contact our support team.",
            styles["Normal"],
        )
        elements.append(thank_you)

        # Footer with disclaimer
        disclaimer = Paragraph(
            "<font size=8>Payments are non-refundable and are subject to our terms and conditions.</font>",
            styles["Normal"],
        )
        elements.append(disclaimer)

        doc.build(elements)

        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"receipt_{payment.user.username}_{payment.id}.pdf",
            content_type="application/pdf",
        )

    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        messages.error(request, "Payment not found.")
        return redirect(reverse('soma:fees'))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messages.error(request, "An unexpected error occurred while generating receipt.")
        return redirect(reverse('soma:fees'))


@login_required
def access_recording(request, recording_id):
    recording = get_object_or_404(Recording, id=recording_id, is_deleted=False)
    return redirect(recording.recording_link)


@login_required
def recordings(request):
    user = request.user
    context = {"user": user}  # Initialize context
    try:
        active_enrollment_status = EnrollmentStatus.objects.get(
            name="Active", 
            is_deleted=False
        )
        active_enrollments = Enrollment.objects.filter(
            user=user, 
            enrollment_status=active_enrollment_status, 
            is_deleted=False
        )

        if not active_enrollments.exists():
            messages.warning(
                request, 
                "You need an active enrollment to view the recordings."
            )
            return redirect(reverse('soma:student_home'))

        course_ids = [enrollment.course_id for enrollment in active_enrollments]
        session_ids = [
            enrollment.session_id 
            for enrollment in active_enrollments 
            if enrollment.session_id
        ]
        
        recordings = Recording.objects.filter(
            course_id__in=course_ids,
            session_id__in=session_ids,
            is_deleted=False
        )

        context["recordings"] = recordings

    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        messages.error(request, "Could not retrieve recording information.")
        return redirect(reverse('soma:student_home'))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messages.error(
            request, 
            "An unexpected error occurred while retrieving recording information."
        )
        return redirect(reverse('soma:student_home'))

    return render(request, "soma/recordings.html", context)


@login_required
def materials(request):
    user = request.user
    context = {"user": user}  # Initialize context
    try:
        active_enrollment_status = EnrollmentStatus.objects.get(name="Active", is_deleted=False)  # Use get()
        active_enrollments = Enrollment.objects.filter(
            user=user, enrollment_status=active_enrollment_status, is_deleted=False
        )

        if not active_enrollments.exists():
            messages.warning(request, "You need an active enrollment to view the materials.")
            return redirect(reverse('soma:student_home'))

        course_ids = [enrollment.course_id for enrollment in active_enrollments]
        materials = LearningMaterial.objects.filter(course_id__in=course_ids, is_deleted=False)

        context["materials"] = materials

    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        messages.error(request, "Could not retrieve materials.")
        return redirect(reverse('soma:student_home'))  # Or handle differently

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messages.error(request, "An unexpected error occurred while retrieving materials.")
        return redirect(reverse('soma:student_home'))  # Or handle differently

    return render(request, "soma/materials.html", context)


@login_required
def access_material(request, material_id):
    user = request.user
    context = {"user": user}  # Initialize context
    try:
        material = get_object_or_404(LearningMaterial, id=material_id, is_deleted=False)
        active_enrollment_status = EnrollmentStatus.objects.get(name="Active", is_deleted=False)  # Use get()
        active_enrollment = Enrollment.objects.filter(
            user=user,
            course=material.course,
            enrollment_status=active_enrollment_status,
            is_deleted=False
        ).first()

        if not active_enrollment:
            messages.warning(request, "You need an active enrollment to access the material.")
            return redirect(reverse('soma:student_home'))

        return redirect(material.document_link)

    except ObjectDoesNotExist as e:
        logger.error(f"ObjectDoesNotExist: {e}")
        messages.error(request, "Material or enrollment not found.")
        return redirect(reverse('soma:student_home'))

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messages.error(request, "An unexpected error occurred while accessing the material.")
        return redirect(reverse('soma:student_home'))