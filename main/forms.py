from django import forms


DAY_CHOICES = ((7, "最近 7 天"), (30, "最近 30 天"), (90, "最近 90 天"))


class AnalyticsConversationForm(forms.Form):
    default_days = forms.TypedChoiceField(choices=DAY_CHOICES, coerce=int)


class AnalyticsQuestionForm(forms.Form):
    question = forms.CharField(max_length=1000, strip=True)
    days = forms.TypedChoiceField(choices=DAY_CHOICES, coerce=int)
