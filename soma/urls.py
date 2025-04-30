from django.urls import path
from . import views

app_name = 'soma'

urlpatterns = [
    path('dashboard/', views.student_home, name='student_home'),
    path('register_payments/', views.register_payments, name='register_payments'),
    path('fees/', views.fees, name='fees'),
    path('timetable/', views.timetable, name='timetable'),
    path('enrol/', views.enrol, name='enrol'),
    path('invoice/<int:enrollment_id>/', views.invoice, name='invoice'),
    path('receipt/<int:payment_id>/', views.receipt, name='receipt'),
    path('download_receipt/<int:payment_id>/', views.download_receipt, name='download_receipt'),
    path('access_recording/<int:recording_id>/<str:token>/', views.access_recording, name='access_recording'),
    path('recordings/', views.recordings, name='recordings'),
    path('access_material/<int:material_id>/', views.access_material, name='access_material'),
    path('materials/', views.materials, name='materials'),
    path('get_sessions/', views.get_sessions, name='get_sessions'),
    path('partial_payment_amount_input/', views.partial_payment_amount_input, name='partial_payment_amount_input'),
    path('get_course_fee/', views.get_course_fee, name='get_course_fee'),
]