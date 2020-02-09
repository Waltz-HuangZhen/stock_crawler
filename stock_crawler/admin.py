from django.contrib import admin

from stock_crawler.models import Log
from stock_crawler.settings import ADMIN_WEBSITE_HEADER


admin.AdminSite.site_header = ADMIN_WEBSITE_HEADER
admin.AdminSite.name = ADMIN_WEBSITE_HEADER


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('action', 'time', 'status', 'message', 'duration_ms')
    list_filter = ('action', 'time', 'status')
    date_hierarchy = 'time'
