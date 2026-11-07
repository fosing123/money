import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("finance", "0003_account_choices_and_transaction_indexes"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExpenseAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("analysis_type", models.CharField(choices=[("PLANNED", "Planned purchase"), ("COMPLETED", "Completed expense")], max_length=12)),
                ("description", models.CharField(blank=True, default="", max_length=255)),
                ("category", models.CharField(default="General", max_length=50)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("currency", models.CharField(default="XAF", max_length=10)),
                ("is_essential", models.BooleanField(default=False)),
                ("purchase_date", models.DateField(blank=True, null=True)),
                ("score", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("verdict", models.CharField(choices=[("EXCELLENT", "Excellent"), ("GOOD", "Good"), ("FAIR", "Fair"), ("POOR", "Poor"), ("CRITICAL", "Critical")], max_length=12)),
                ("score_breakdown", models.JSONField(blank=True, default=dict)),
                ("financial_context", models.JSONField(blank=True, default=dict)),
                ("financial_impact", models.JSONField(blank=True, default=dict)),
                ("summary", models.TextField(blank=True, default="")),
                ("reasoning", models.JSONField(blank=True, default=list)),
                ("recommendations", models.JSONField(blank=True, default=list)),
                ("alternatives", models.JSONField(blank=True, default=list)),
                ("next_action", models.CharField(choices=[("PROCEED", "Proceed"), ("ADJUST", "Adjust the plan"), ("POSTPONE", "Postpone"), ("RECOVER", "Review the remaining budget")], default="ADJUST", max_length=12)),
                ("confidence", models.CharField(choices=[("HIGH", "High"), ("MEDIUM", "Medium"), ("LOW", "Low")], default="LOW", max_length=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expense_analyses", to="finance.transaction")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expense_analyses", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="expenseanalysis",
            index=models.Index(fields=["user", "created_at"], name="expense_user_date_idx"),
        ),
        migrations.AddIndex(
            model_name="expenseanalysis",
            index=models.Index(fields=["user", "analysis_type"], name="expense_user_type_idx"),
        ),
    ]
