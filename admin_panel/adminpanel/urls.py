from django.contrib import admin
from django.urls import path

admin.site.site_header = "Blog Management API — Admin"
admin.site.site_title = "Blog API Admin"
admin.site.index_title = "Subscriptions, Billing & Content"

urlpatterns = [
    path("admin/", admin.site.urls),
]
