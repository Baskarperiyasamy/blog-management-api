from django.db import models


class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=120, unique=True)
    password = models.CharField(max_length=255)  # hashed, set by FastAPI — never edited here
    plan = models.ForeignKey(
        "SubscriptionPlan", db_column="plan_id", on_delete=models.DO_NOTHING,
        db_constraint=False, null=True, blank=True, related_name="users",
    )
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.CharField(max_length=255, null=True, blank=True)
    author = models.ForeignKey(
        User, db_column="author_id", on_delete=models.DO_NOTHING,
        db_constraint=False, related_name="posts",
    )
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "posts"

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, db_column="post_id", on_delete=models.DO_NOTHING, db_constraint=False, related_name="comments")
    user = models.ForeignKey(User, db_column="user_id", on_delete=models.DO_NOTHING, db_constraint=False, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "comments"

    def __str__(self):
        return f"Comment #{self.id} on Post #{self.post_id}"


class Like(models.Model):
    post = models.ForeignKey(Post, db_column="post_id", on_delete=models.DO_NOTHING, db_constraint=False, related_name="likes")
    user = models.ForeignKey(User, db_column="user_id", on_delete=models.DO_NOTHING, db_constraint=False, related_name="likes")

    class Meta:
        managed = False
        db_table = "likes"

    def __str__(self):
        return f"Like #{self.id}"


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.FloatField()
    duration_days = models.IntegerField(default=30)
    max_posts = models.IntegerField(null=True, blank=True, help_text="Blank = unlimited")
    max_images_per_post = models.IntegerField(null=True, blank=True, help_text="Blank = unlimited")
    max_likes = models.IntegerField(null=True, blank=True, help_text="Blank = unlimited")
    max_comments = models.IntegerField(null=True, blank=True, help_text="Blank = unlimited")

    class Meta:
        managed = False
        db_table = "subscription_plans"
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return self.name.title()


class BillingHistory(models.Model):
    user = models.ForeignKey(User, db_column="user_id", on_delete=models.DO_NOTHING, db_constraint=False, related_name="billing_history")
    plan = models.ForeignKey(SubscriptionPlan, db_column="plan_id", on_delete=models.DO_NOTHING, db_constraint=False, related_name="billing_history")
    transaction_id = models.CharField(max_length=50, unique=True)
    amount = models.FloatField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    invoice_path = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "billing_history"
        verbose_name = "Billing History"
        verbose_name_plural = "Billing History"

    def __str__(self):
        return f"{self.transaction_id} — {self.user.username if self.user_id else '?'}"
