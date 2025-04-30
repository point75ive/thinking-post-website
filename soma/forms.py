from django import forms
from .models import Fee, Session, Course

class EnrolForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_deleted=False),
        label="Select a Course",
        empty_label="Select a course",
        widget=forms.Select(attrs={
            'hx-get': '/get_sessions/',
            'hx-target': '#session-select',
            'hx-trigger': 'change'
        })
    )
    
    session = forms.ModelChoiceField(
        queryset=Session.objects.none(),  # Initially no sessions
        label="Select a Session",
        empty_label="Select a session",
        widget=forms.Select(attrs={'id': 'session-select'})
    )
    
    phone_no = forms.CharField(
        label="Phone Number",
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': "Enter your phone number"})
    )
    
    payment_option = forms.ChoiceField(
        label="Payment Option",
        choices=[('full', 'Full Payment'), ('half', 'Partial Payment')],
        widget=forms.RadioSelect,
        initial='full'
    )
    
    partial_payment_amount = forms.DecimalField(
        label="Partial Payment Amount",
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'input',
            'placeholder': "Enter amount",
            'style': 'display:none;'  # Will be shown via JavaScript
        })
    )
    
    comments = forms.CharField(
        label="Additional Comments or Special Requests",
        required=False,
        widget=forms.Textarea(attrs={'placeholder': "Enter any comments or requests"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'course' in self.data:
            try:
                course_id = int(self.data['course'])
                self.fields['session'].queryset = Session.objects.filter(
                    course_id=course_id,
                    is_deleted=False
                )
            except (ValueError, TypeError):
                pass  # Invalid course ID, leave queryset empty

class InvoiceForm(forms.Form):
    mpesa_ref = forms.CharField(
        label="MPESA Transaction Code",
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter MPESA transaction code',
            'class': 'input'
        })
    )
    
    payment_amount = forms.DecimalField(
        label="Payment Amount",
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'input',
            'step': '0.01'
        })
    )

    def clean_payment_amount(self):
        amount = self.cleaned_data['payment_amount']
        if amount < 100:  # Set your minimum payment amount
            raise forms.ValidationError("Minimum payment is Ksh 100")
        return amount

class PaymentForm(forms.Form):
    fee_id = forms.IntegerField()