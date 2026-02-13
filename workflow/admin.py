from django.contrib import admin
from .models import Document
from .models import AuditLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "created_by__username")
    ordering = ("-created_at",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "action", "actor", "created_at")
    list_filter = ("action", "created_at")
    ordering = ("-created_at",)
