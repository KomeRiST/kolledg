from django.contrib import admin
# from import_export.admin import ImportExportModelAdmin
# from import_export import resources
from . import models


# class GroupsResource(resources.ModelResource):
#     class Meta:
#         model = models.Groups


# class GroupsAdmin(ImportExportModelAdmin):
#     resource_class = GroupsResource
#

# class StudResource(resources.ModelResource):
#     class Meta:
#         model = models.Students
#
#
# class StudFamInline(admin.TabularInline):
#     model = models.StudFam
#     extra = 1
#
#
# class StudAdmin(ImportExportModelAdmin):
#     resource_class = StudResource
#
#
# class StudAdmin2(admin.ModelAdmin):
#     inlines = [StudFamInline]


class PrepodFamInline(admin.TabularInline):
    model = models.PrepodFam
    extra = 1


class PrepodAdmin(admin.ModelAdmin):
    inlines = [PrepodFamInline]


# admin.site.register(models.Groups, GroupsAdmin)
admin.site.register(models.Groups)
admin.site.register(models.Kompetencii)
# admin.site.register(models.Students, StudAdmin2)
admin.site.register(models.Prepods, PrepodAdmin)
