"""Pydantic models for InBody scan results."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SegmentalAnalysis(BaseModel):
    """Segmental analysis for body parts."""

    right_arm_lean: Optional[float] = Field(None, description='Right arm lean mass in kg')
    left_arm_lean: Optional[float] = Field(None, description='Left arm lean mass in kg')
    trunk_lean: Optional[float] = Field(None, description='Trunk lean mass in kg')
    right_leg_lean: Optional[float] = Field(None, description='Right leg lean mass in kg')
    left_leg_lean: Optional[float] = Field(None, description='Left leg lean mass in kg')

    right_arm_fat: Optional[float] = Field(None, description='Right arm fat mass in kg')
    left_arm_fat: Optional[float] = Field(None, description='Left arm fat mass in kg')
    trunk_fat: Optional[float] = Field(None, description='Trunk fat mass in kg')
    right_leg_fat: Optional[float] = Field(None, description='Right leg fat mass in kg')
    left_leg_fat: Optional[float] = Field(None, description='Left leg fat mass in kg')


class InBodyResult(BaseModel):
    """Complete InBody scan result."""

    # Basic Information
    scan_date: datetime = Field(..., description='Date and time of the scan')
    height: float = Field(..., description='Height in cm')
    weight: float = Field(..., description='Weight in kg')
    age: Optional[int] = Field(None, description='Age in years')
    gender: Optional[str] = Field(None, description='Gender (Male/Female)')

    # Body Composition
    muscle_mass: Optional[float] = Field(None, description='Total muscle mass in kg')
    body_fat_mass: Optional[float] = Field(None, description='Total body fat mass in kg')
    body_fat_percentage: Optional[float] = Field(None, description='Body fat percentage')

    # Body Water and FFM
    total_body_water: Optional[float] = Field(None, description='Total body water in liters')
    fat_free_mass: Optional[float] = Field(None, description='Fat-free mass in kg')

    # Health Metrics
    bmi: Optional[float] = Field(None, description='Body Mass Index')
    bmr: Optional[float] = Field(None, description='Basal Metabolic Rate in kcal')
    visceral_fat_level: Optional[float] = Field(None, description='Visceral fat level')

    # Additional Metrics
    pbf: Optional[float] = Field(None, description='Percent body fat')
    whr: Optional[float] = Field(None, description='Waist-hip ratio')

    # Score (unified from InBody score/Fitness score across different models)
    body_score: Optional[int] = Field(None, description='Body composition score (InBody/Fitness score)')

    # Control Recommendations
    muscle_control: Optional[float] = Field(None, description='Muscle control recommendation in kg')
    fat_control: Optional[float] = Field(None, description='Fat control recommendation in kg')

    # Segmental Analysis
    segmental: Optional[SegmentalAnalysis] = Field(None, description='Segmental body analysis')

    # Raw text for debugging
    raw_text: Optional[str] = Field(None, description='Raw extracted text from image')


class ProcessedImage(BaseModel):
    """Metadata for processed images."""

    file_path: str = Field(..., description='Path to the image file')
    file_hash: str = Field(..., description='SHA-256 hash of the image file')
    processed_at: datetime = Field(..., description='When the image was processed')
    success: bool = Field(..., description='Whether processing was successful')
    error_message: Optional[str] = Field(None, description='Error message if processing failed')
