"""Image processing using OpenAI GPT Vision to extract InBody scan data."""

import base64
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import openai
from pydantic import ValidationError

from inbody_to_sqlite.models import InBodyResult, SegmentalAnalysis


class InBodyImageProcessor:
    """Process InBody scan images using OpenAI GPT-4 Vision."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the image processor with OpenAI API key."""
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

        # JSON schema for structured output
        self.json_schema = {
            'type': 'object',
            'properties': {
                'scan_date': {
                    'type': 'string',
                    'description': 'Date and time of scan in ISO format (YYYY-MM-DD HH:MM:SS)',
                },
                'height': {'type': 'number', 'description': 'Height in centimeters'},
                'weight': {'type': 'number', 'description': 'Weight in kilograms'},
                'age': {'type': ['number', 'null'], 'description': 'Age in years'},
                'gender': {
                    'type': ['string', 'null'],
                    'description': 'Gender (Male/Female)',
                },
                'muscle_mass': {
                    'type': ['number', 'null'],
                    'description': 'Total muscle mass in kg',
                },
                'body_fat_mass': {
                    'type': ['number', 'null'],
                    'description': 'Total body fat mass in kg',
                },
                'body_fat_percentage': {
                    'type': ['number', 'null'],
                    'description': 'Body fat percentage',
                },
                'total_body_water': {
                    'type': ['number', 'null'],
                    'description': 'Total body water in liters',
                },
                'fat_free_mass': {
                    'type': ['number', 'null'],
                    'description': 'Fat-free mass in kg',
                },
                'bmi': {'type': ['number', 'null'], 'description': 'Body Mass Index'},
                'bmr': {
                    'type': ['number', 'null'],
                    'description': 'Basal Metabolic Rate in kcal',
                },
                'visceral_fat_level': {
                    'type': ['number', 'null'],
                    'description': 'Visceral fat level',
                },
                'pbf': {'type': ['number', 'null'], 'description': 'Percent body fat'},
                'whr': {'type': ['number', 'null'], 'description': 'Waist-hip ratio'},
                'body_score': {
                    'type': ['integer', 'null'],
                    'description': 'Body composition score (may be called InBody score or Fitness score)',
                },
                'muscle_control': {
                    'type': ['number', 'null'],
                    'description': 'Muscle control recommendation in kg',
                },
                'fat_control': {
                    'type': ['number', 'null'],
                    'description': 'Fat control recommendation in kg',
                },
                'segmental': {
                    'type': ['object', 'null'],
                    'properties': {
                        'right_arm_lean': {'type': ['number', 'null']},
                        'left_arm_lean': {'type': ['number', 'null']},
                        'trunk_lean': {'type': ['number', 'null']},
                        'right_leg_lean': {'type': ['number', 'null']},
                        'left_leg_lean': {'type': ['number', 'null']},
                        'right_arm_fat': {'type': ['number', 'null']},
                        'left_arm_fat': {'type': ['number', 'null']},
                        'trunk_fat': {'type': ['number', 'null']},
                        'right_leg_fat': {'type': ['number', 'null']},
                        'left_leg_fat': {'type': ['number', 'null']},
                    },
                },
            },
            'required': ['scan_date', 'height', 'weight'],
        }

    def calculate_image_hash(self, image_path: Path) -> str:
        """Calculate SHA-256 hash of the image file for caching."""
        sha256_hash = hashlib.sha256()
        with open(image_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def encode_image_to_base64(self, image_path: Path) -> str:
        """Encode image to base64 for OpenAI API."""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def process_image(self, image_path: Path) -> tuple[Optional[InBodyResult], str]:
        """
        Process an InBody scan image and extract structured data.

        Returns:
            tuple: (InBodyResult or None, raw_text_response)
        """
        try:
            # Verify image file exists and is readable
            if not image_path.exists():
                raise FileNotFoundError(f'Image file not found: {image_path}')

            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_path)

            # Prepare the prompt
            prompt = """
            You are analyzing an InBody body composition scan result. This is a printed receipt/report from an InBody machine.
            
            Please extract ALL the numerical data and information you can see in this InBody scan result.
            Pay attention to:
            
            1. Basic info: Date, height, weight, age, gender
            2. Body composition: muscle mass, body fat mass, body fat percentage
            3. Body water and fat-free mass (FFM, TBW)
            4. Health metrics: BMI, BMR, visceral fat level
            5. Additional metrics: PBF, WHR if present
            6. Scores: InBody score, fitness score
            7. Control recommendations: muscle control, fat control
            8. Segmental analysis: lean and fat mass for arms, trunk, legs
            
            The scan might be in different languages (English, Polish, etc.) but extract the numerical values.
            Some fields might not be present in all InBody models - that's okay, just extract what you can see.
            
            IMPORTANT: For the score field, different InBody models call it either "InBody Score" or "Fitness Score" - 
            these are the same metric. Extract whichever one is present and put it in the "body_score" field.
            
            For dates, convert to ISO format (YYYY-MM-DD HH:MM:SS). If time is not specified, use 00:00:00.
            For segmental analysis, look for body part measurements (arms, trunk, legs).
            
            Return the data in the specified JSON format. If a value is not visible or present, use null.
            """

            response = self.client.chat.completions.create(
                model='gpt-4.1',
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt},
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{base64_image}',
                                    'detail': 'high',
                                },
                            },
                        ],
                    }
                ],
                response_format={
                    'type': 'json_schema',
                    'json_schema': {
                        'name': 'inbody_result',
                        'schema': self.json_schema,
                    },
                },
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistent extraction
            )

            # Get the response content
            raw_response = response.choices[0].message.content

            if not raw_response:
                return None, 'Empty response from OpenAI'

            # Parse JSON response
            try:
                data = json.loads(raw_response)
            except json.JSONDecodeError as e:
                return None, f'JSON decode error: {e}\nRaw response: {raw_response}'

            # Convert to our Pydantic model
            try:
                # Handle segmental data
                segmental_data = None
                if data.get('segmental'):
                    segmental_data = SegmentalAnalysis(**data['segmental'])

                # Parse date
                scan_date = datetime.fromisoformat(data['scan_date'])

                result = InBodyResult(
                    scan_date=scan_date,
                    height=data['height'],
                    weight=data['weight'],
                    age=data.get('age'),
                    gender=data.get('gender'),
                    muscle_mass=data.get('muscle_mass'),
                    body_fat_mass=data.get('body_fat_mass'),
                    body_fat_percentage=data.get('body_fat_percentage'),
                    total_body_water=data.get('total_body_water'),
                    fat_free_mass=data.get('fat_free_mass'),
                    bmi=data.get('bmi'),
                    bmr=data.get('bmr'),
                    visceral_fat_level=data.get('visceral_fat_level'),
                    pbf=data.get('pbf'),
                    whr=data.get('whr'),
                    body_score=data.get('body_score'),
                    muscle_control=data.get('muscle_control'),
                    fat_control=data.get('fat_control'),
                    segmental=segmental_data,
                    raw_text=raw_response,
                )

                return result, raw_response

            except ValidationError as e:
                return None, f'Validation error: {e}\nRaw response: {raw_response}'

        except Exception as e:
            return None, f'Error processing image: {e}'

    @staticmethod
    def get_supported_extensions() -> list[str]:
        """Get list of supported image file extensions."""
        return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
