from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ExpenseAnalysis(models.Model):
    """A saved, explainable assessment of a planned or completed expense."""

    PLANNED = "PLANNED"
    COMPLETED = "COMPLETED"
    ANALYSIS_TYPES = [(PLANNED, "Planned purchase"), (COMPLETED, "Completed expense")]

    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    CRITICAL = "CRITICAL"
    VERDICTS = [
        (EXCELLENT, "Excellent"),
        (GOOD, "Good"),
        (FAIR, "Fair"),
        (POOR, "Poor"),
        (CRITICAL, "Critical"),
    ]

    PROCEED = "PROCEED"
    ADJUST = "ADJUST"
    POSTPONE = "POSTPONE"
    RECOVER = "RECOVER"
    NEXT_ACTIONS = [
        (PROCEED, "Proceed"),
        (ADJUST, "Adjust the plan"),
        (POSTPONE, "Postpone"),
        (RECOVER, "Review the remaining budget"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expense_analyses",
    )
    transaction = models.ForeignKey(
        "finance.Transaction",
        on_delete=models.SET_NULL,
        related_name="expense_analyses",
        blank=True,
        null=True,
    )
    analysis_type = models.CharField(max_length=12, choices=ANALYSIS_TYPES)
    description = models.CharField(max_length=255, blank=True, default="")
    category = models.CharField(max_length=50, default="General")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default="XAF")
    is_essential = models.BooleanField(default=False)
    purchase_date = models.DateField(blank=True, null=True)
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    verdict = models.CharField(max_length=12, choices=VERDICTS)
    score_breakdown = models.JSONField(default=dict, blank=True)
    financial_context = models.JSONField(default=dict, blank=True)
    financial_impact = models.JSONField(default=dict, blank=True)
    summary = models.TextField(blank=True, default="")
    reasoning = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    alternatives = models.JSONField(default=list, blank=True)
    next_action = models.CharField(max_length=12, choices=NEXT_ACTIONS, default=ADJUST)
    confidence = models.CharField(
        max_length=8,
        choices=[("HIGH", "High"), ("MEDIUM", "Medium"), ("LOW", "Low")],
        default="LOW",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"], name="expense_user_date_idx"),
            models.Index(fields=["user", "analysis_type"], name="expense_user_type_idx"),
        ]

    def clean(self):
        if self.transaction_id:
            if self.transaction.owner_id != self.user_id:
                raise ValidationError({"transaction": "This transaction does not belong to this user."})
            if self.analysis_type != self.COMPLETED or self.transaction.kind != "expense":
                raise ValidationError({"transaction": "Only completed expense analyses can reference an expense transaction."})
            if self.transaction.currency.upper() != self.currency.upper():
                raise ValidationError({"currency": "The analysis and transaction currencies must match."})

        if self.analysis_type == self.PLANNED and self.transaction_id:
            raise ValidationError({"transaction": "A planned purchase must not be linked to a completed transaction."})

    def __str__(self):
        label = self.description or self.category
        return f"{label} · {self.score}/100 · {self.user}"



class AIPersonalization(models.Model):
    """A member's preferred coaching voice and future direction for TIANA."""

    VOICE_STYLES = [
        ("friendly", "Friendly"),
        ("fatherly", "Fatherly"),
        ("motherly", "Motherly"),
        ("mentor", "Mentor"),
    ]
    AMBITIONS = [
        ("financial_freedom", "Become financially independent"),
        ("millionaire", "Build substantial wealth"),
        ("business_owner", "Start or grow a business"),
        ("career", "Build a successful career"),
        ("education", "Complete my education or training"),
        ("support_family", "Support my family"),
        ("own_home", "Own a home or property"),
        ("other", "Something else"),
    ]
    STAGES = [
        ("student", "Student"),
        ("training", "Learning a skill or trade"),
        ("employed", "Employed"),
        ("self_employed", "Self-employed"),
        ("job_seeking", "Looking for work"),
        ("other", "Other"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_personalization",
    )
    voice_style = models.CharField(max_length=12, choices=VOICE_STYLES, default="friendly")
    ambition = models.CharField(max_length=24, choices=AMBITIONS, blank=True, default="")
    current_stage = models.CharField(max_length=16, choices=STAGES, blank=True, default="")
    future_vision = models.CharField(max_length=240, blank=True, default="")
    desired_career = models.CharField(max_length=120, blank=True, default="")
    why_it_matters = models.CharField(max_length=180, blank=True, default="")
    setup_completed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI personalisation"
        verbose_name_plural = "AI personalisations"

    def __str__(self):
        return f"TIANA preferences · {self.user}"
