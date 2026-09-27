from django.contrib import admin
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from apps.governance.models import (
    Candidate,
    CommitteeMember,
    Election,
    HandoverRecord,
    NoConfidenceMotion,
    OathRecord,
    SubCommittee,
    Program,
    ProgramImage,
)
from apps.members.models import Household, Member


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 0
    autocomplete_fields = ["member"]


class OathRecordInline(admin.TabularInline):
    model = OathRecord
    extra = 0


@admin.register(CommitteeMember)
class CommitteeMemberAdmin(admin.ModelAdmin):
    list_display = ["member_name", "member_type", "position", "gender", "term_start", "term_end", "status"]
    list_filter = ["position", "status", "content_type"]
    search_fields = ["member_object__household_head_name", "member_object__full_name"]
    filter_horizontal = ["subcommittees"]
    inlines = [OathRecordInline]

    fieldsets = (
        (
            "Member Selection",
            {
                "fields": ("content_type", "object_id"),
                "description": "Select either a Household or Member. The generic relation will determine which model is linked.",
            },
        ),
        (
            "Committee Details",
            {"fields": ("position", "gender", "caste_ethnicity", "term_start", "term_end", "status", "photo")},
        ),
        ("Sub-committees", {"fields": ("subcommittees",)}),
    )

    def member_name(self, obj):
        """Display member name from either Household or Member"""
        return obj.get_member_name()

    member_name.short_description = "Member Name"

    def member_type(self, obj):
        """Display the member type (Household or Member)"""
        if obj.content_type:
            return obj.content_type.model.capitalize()
        return "—"

    member_type.short_description = "Type"

    def get_search_results(self, request, queryset, search_term):
        """
        Override search to support both Household and Member models.
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if search_term:
            # Get ContentType for both models
            household_ct = ContentType.objects.get_for_model(Household)
            member_ct = ContentType.objects.get_for_model(Member)

            # Search in both Household and Member tables
            household_ids = Household.objects.filter(household_head_name__icontains=search_term).values_list("id", flat=True)

            member_ids = Member.objects.filter(full_name__icontains=search_term).values_list("id", flat=True)

            # Build Q objects for each model
            q_objects = Q()

            if household_ids:
                q_objects |= Q(content_type=household_ct, object_id__in=household_ids)

            if member_ids:
                q_objects |= Q(content_type=member_ct, object_id__in=member_ids)

            queryset = queryset.filter(q_objects)

        return queryset, use_distinct


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ["election_date", "status"]
    inlines = [CandidateInline]


@admin.register(SubCommittee)
class SubCommitteeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    filter_horizontal = ["committee_members"]


@admin.register(OathRecord)
class OathRecordAdmin(admin.ModelAdmin):
    list_display = ["committee_member", "oath_date"]


@admin.register(NoConfidenceMotion)
class NoConfidenceMotionAdmin(admin.ModelAdmin):
    list_display = ["target_type", "target_committee_member", "signatures_count", "assembly_decision"]
    list_filter = ["target_type", "assembly_decision"]


@admin.register(HandoverRecord)
class HandoverRecordAdmin(admin.ModelAdmin):
    list_display = ["outgoing_committee_member", "incoming_committee_member", "deadline_date", "status"]
    list_filter = ["status"]


from django.contrib import admin
from django.utils.html import format_html
from .models import Program, ProgramImage


class ProgramImageInline(admin.TabularInline):
    model = ProgramImage
    extra = 1
    fields = ["image", "image_preview", "caption", "order"]
    readonly_fields = ["image_preview"]
    ordering = ["order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 60px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Preview"


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "image_count", "created_at"]
    list_filter = ["date"]
    search_fields = ["title", "description"]
    date_hierarchy = "date"
    inlines = [ProgramImageInline]

    def image_count(self, obj):
        return obj.images.count()

    image_count.short_description = "Images"


@admin.register(ProgramImage)
class ProgramImageAdmin(admin.ModelAdmin):
    list_display = ["program", "caption", "order", "image_preview"]
    list_filter = ["program"]
    search_fields = ["caption", "program__title"]
    ordering = ["program", "order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 40px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Preview"
