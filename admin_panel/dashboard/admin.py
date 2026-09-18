from django.contrib import admin
from django.utils.html import format_html

from .models import User, Post, Comment, Like, SubscriptionPlan, BillingHistory


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "current_plan", "created_at")
    list_filter = ("plan",)
    search_fields = ("username", "email")
    readonly_fields = ("password",)  # hashed by FastAPI — never edit here

    def current_plan(self, obj):
        return obj.plan.name.title() if obj.plan_id else "— none —"
    current_plan.short_description = "Plan"

    def has_add_permission(self, request):
        # Users register through the API (POST /auth/register), not here.
        return False


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_days", "max_posts", "max_images_per_post", "max_likes", "max_comments", "subscriber_count")
    ordering = ("price",)

    def subscriber_count(self, obj):
        return obj.users.count()
    subscriber_count.short_description = "Active Subscribers"

    def has_add_permission(self, request):
        # The 3 plans (basic/premium/pro) are seeded once by FastAPI at startup.
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "user", "plan", "amount", "start_date", "end_date", "invoice_link")
    list_filter = ("plan",)
    search_fields = ("transaction_id", "user__username")
    ordering = ("-created_at",)

    def invoice_link(self, obj):
        if not obj.invoice_path:
            return "—"
        url = f"http://127.0.0.1:8000/media/{obj.invoice_path}"
        return format_html('<a href="{}" target="_blank">View Invoice PDF</a>', url)
    invoice_link.short_description = "Invoice"

    def has_add_permission(self, request):
        # Billing rows are created only via POST /subscriptions/subscribe.
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    search_fields = ("title", "content")

    def has_add_permission(self, request):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "text", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user")

    def has_add_permission(self, request):
        return False
