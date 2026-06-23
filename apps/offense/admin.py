from django.contrib import admin

from apps.offense.models import (
    EvidenceItem,
    HearingRecord,
    InformantReward,
    OffenseReport,
    PatrolLog,
)


class EvidenceItemInline(admin.TabularInline):
    model = EvidenceItem
    extra = 0


class HearingRecordInline(admin.TabularInline):
    model = HearingRecord
    extra = 0


@admin.register(OffenseReport)
class OffenseReportAdmin(admin.ModelAdmin):
    list_display = ["accused_name", "offense_type", "report_date", "status", "fine_amount", "resolution"]
    list_filter = ["status", "offense_type"]
    search_fields = ["accused_name", "offense_type"]
    inlines = [EvidenceItemInline, HearingRecordInline]
    autocomplete_fields = ["reported_by", "informant"]


@admin.register(EvidenceItem)
class EvidenceItemAdmin(admin.ModelAdmin):
    list_display = ["offense", "item_type", "confiscated_date"]
    list_filter = ["item_type"]


@admin.register(HearingRecord)
class HearingRecordAdmin(admin.ModelAdmin):
    list_display = ["offense", "hearing_date", "outcome"]


@admin.register(InformantReward)
class InformantRewardAdmin(admin.ModelAdmin):
    list_display = ["offense", "informant", "reward_amount", "paid_date"]


@admin.register(PatrolLog)
class PatrolLogAdmin(admin.ModelAdmin):
    list_display = ["watcher", "patrol_date", "offense"]
    autocomplete_fields = ["watcher", "offense"]
