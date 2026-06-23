from django.contrib import admin

from apps.governance.models import (
    Candidate,
    CommitteeMember,
    Election,
    HandoverRecord,
    NoConfidenceMotion,
    OathRecord,
    SubCommittee,
)


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 0
    autocomplete_fields = ["member"]


class OathRecordInline(admin.TabularInline):
    model = OathRecord
    extra = 0


@admin.register(CommitteeMember)
class CommitteeMemberAdmin(admin.ModelAdmin):
    list_display = ["member", "position", "gender", "term_start", "term_end", "status"]
    list_filter = ["position", "status"]
    search_fields = ["member__full_name"]
    autocomplete_fields = ["member"]
    filter_horizontal = ["subcommittees"]
    inlines = [OathRecordInline]


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
