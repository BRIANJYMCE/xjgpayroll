from django import forms
from .models import WorkAssignment, WorkType
from django.contrib.auth.models import User

class WorkTypeForm(forms.ModelForm):
    class Meta:
        model = WorkType
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'border rounded p-2 w-full'})
        }

class WorkAssignmentForm(forms.ModelForm):
    class Meta:
        model = WorkAssignment
        fields = ["user", "work_types"]
        widgets = {
            'work_types': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active WorkTypes
        self.fields['work_types'].queryset = WorkType.objects.filter(is_active=True)

class AdminWorkAssignmentForm(forms.ModelForm):
  
    class Meta:
        model = WorkAssignment
        fields = ["work_types"] 
        widgets = {
            'work_types': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['work_types'].queryset = WorkType.objects.filter(is_active=True)

class AdminSingleWorkAssignmentForm(forms.ModelForm):
    work_type = forms.ModelChoiceField(
        queryset=WorkType.objects.none(),
        widget=forms.Select(),
    )

    class Meta:
        model = WorkAssignment
        fields = ["work_type"]
        widgets = {
            "work_type": forms.Select(attrs={
                "class": (
                    "w-full px-4 py-3 text-sm border border-gray-200 rounded-lg "
                    "bg-white text-gray-900 placeholder-gray-400 focus:outline-none "
                    "focus:ring-2 focus:ring-blue-500 focus:border-blue-500 "
                    "transition-all duration-200 hover:border-gray-300 cursor-pointer"
                )
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            assignment = WorkAssignment.objects.filter(user=user).first()
            assigned_ids = assignment.work_types.values_list('id', flat=True) if assignment else []
            self.fields['work_type'].queryset = WorkType.objects.filter(is_active=True).exclude(id__in=assigned_ids)
        else:
            self.fields['work_type'].queryset = WorkType.objects.filter(is_active=True)

