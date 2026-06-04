"""API Serializers for dashboard endpoints"""
from rest_framework import serializers
from parser.models import CVUpload, ExtractedSkill
from analysis.models import SkillGapReport, GapItem
from roadmap.models import Roadmap, RoadmapItem, Resource


class CVUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVUpload
        fields = ['id', 'original_filename', 'parse_status', 'uploaded_at', 'parsed_at']
        read_only_fields = ['id', 'uploaded_at', 'parsed_at']


class ExtractedSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedSkill
        fields = ['id', 'skill_name', 'normalized_name', 'confidence_score']


class GapItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GapItem
        fields = ['skill_name', 'demand_frequency', 'similarity_score', 'priority_rank']


class SkillGapReportSerializer(serializers.ModelSerializer):
    gap_items = GapItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = SkillGapReport
        fields = ['id', 'readiness_score', 'total_jobs_matched', 'status', 'generated_at', 'gap_items']


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['title', 'url', 'platform', 'resource_type']


class RoadmapItemSerializer(serializers.ModelSerializer):
    resources = ResourceSerializer(many=True, read_only=True)
    
    class Meta:
        model = RoadmapItem
        fields = ['skill_name', 'week_number', 'description', 'resources']


class RoadmapSerializer(serializers.ModelSerializer):
    items = RoadmapItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Roadmap
        fields = ['id', 'generated_by', 'created_at', 'items']
