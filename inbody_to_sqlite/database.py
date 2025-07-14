"""Database operations for InBody scan results."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from inbody_to_sqlite.models import InBodyResult, ProcessedImage


class InBodyDatabase:
    """Database manager for InBody scan results."""

    def __init__(self, db_path: str = 'inbody_results.db'):
        """Initialize database connection and create tables if needed."""
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            # Create processed_images table for caching
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL,
                    processed_at TIMESTAMP NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create inbody_results table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inbody_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT NOT NULL,
                    scan_date TIMESTAMP NOT NULL,
                    height REAL NOT NULL,
                    weight REAL NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    
                    -- Body Composition
                    muscle_mass REAL,
                    body_fat_mass REAL,
                    body_fat_percentage REAL,
                    
                    -- Body Water and FFM
                    total_body_water REAL,
                    fat_free_mass REAL,
                    
                    -- Health Metrics
                    bmi REAL,
                    bmr REAL,
                    visceral_fat_level REAL,
                    
                    -- Additional Metrics
                    pbf REAL,
                    whr REAL,
                    
                    -- Score (unified from InBody/Fitness score)
                    body_score INTEGER,
                    
                    -- Control Recommendations
                    muscle_control REAL,
                    fat_control REAL,
                    
                    -- Segmental Analysis - Lean Mass
                    right_arm_lean REAL,
                    left_arm_lean REAL,
                    trunk_lean REAL,
                    right_leg_lean REAL,
                    left_leg_lean REAL,
                    
                    -- Segmental Analysis - Fat Mass
                    right_arm_fat REAL,
                    left_arm_fat REAL,
                    trunk_fat REAL,
                    right_leg_fat REAL,
                    left_leg_fat REAL,
                    
                    -- Raw data
                    raw_text TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (file_hash) REFERENCES processed_images (file_hash)
                )
            """)

            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON processed_images (file_hash)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_scan_date ON inbody_results (scan_date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_result_file_hash ON inbody_results (file_hash)')

            conn.commit()

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()

    def is_image_processed(self, file_hash: str) -> bool:
        """Check if an image has already been processed."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT 1 FROM processed_images WHERE file_hash = ? AND success = 1',
                (file_hash,),
            )
            return cursor.fetchone() is not None

    def record_processed_image(self, processed_image: ProcessedImage) -> int:
        """Record that an image has been processed."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO processed_images 
                (file_path, file_hash, processed_at, success, error_message)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    processed_image.file_path,
                    processed_image.file_hash,
                    processed_image.processed_at,
                    processed_image.success,
                    processed_image.error_message,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def save_inbody_result(self, result: InBodyResult, file_hash: str) -> int:
        """Save InBody scan result to database."""
        # Extract segmental values
        segmental = result.segmental
        right_arm_lean = segmental.right_arm_lean if segmental else None
        left_arm_lean = segmental.left_arm_lean if segmental else None
        trunk_lean = segmental.trunk_lean if segmental else None
        right_leg_lean = segmental.right_leg_lean if segmental else None
        left_leg_lean = segmental.left_leg_lean if segmental else None
        right_arm_fat = segmental.right_arm_fat if segmental else None
        left_arm_fat = segmental.left_arm_fat if segmental else None
        trunk_fat = segmental.trunk_fat if segmental else None
        right_leg_fat = segmental.right_leg_fat if segmental else None
        left_leg_fat = segmental.left_leg_fat if segmental else None

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO inbody_results (
                    file_hash, scan_date, height, weight, age, gender,
                    muscle_mass, body_fat_mass, body_fat_percentage,
                    total_body_water, fat_free_mass,
                    bmi, bmr, visceral_fat_level,
                    pbf, whr,
                    body_score,
                    muscle_control, fat_control,
                    right_arm_lean, left_arm_lean, trunk_lean, right_leg_lean, left_leg_lean,
                    right_arm_fat, left_arm_fat, trunk_fat, right_leg_fat, left_leg_fat,
                    raw_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    file_hash,
                    result.scan_date,
                    result.height,
                    result.weight,
                    result.age,
                    result.gender,
                    result.muscle_mass,
                    result.body_fat_mass,
                    result.body_fat_percentage,
                    result.total_body_water,
                    result.fat_free_mass,
                    result.bmi,
                    result.bmr,
                    result.visceral_fat_level,
                    result.pbf,
                    result.whr,
                    result.body_score,
                    result.muscle_control,
                    result.fat_control,
                    right_arm_lean,
                    left_arm_lean,
                    trunk_lean,
                    right_leg_lean,
                    left_leg_lean,
                    right_arm_fat,
                    left_arm_fat,
                    trunk_fat,
                    right_leg_fat,
                    left_leg_fat,
                    result.raw_text,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_results(self) -> list[dict[str, Any]]:
        """Get all InBody results from database."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT r.*, p.file_path 
                FROM inbody_results r
                JOIN processed_images p ON r.file_hash = p.file_hash
                ORDER BY r.scan_date DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            return results

    def get_processing_stats(self) -> dict[str, int]:
        """Get statistics about processed images."""
        with self.get_connection() as conn:
            stats = {}

            cursor = conn.execute('SELECT COUNT(*) as total FROM processed_images')
            stats['total_processed'] = cursor.fetchone()['total']

            cursor = conn.execute('SELECT COUNT(*) as successful FROM processed_images WHERE success = 1')
            stats['successful'] = cursor.fetchone()['successful']

            cursor = conn.execute('SELECT COUNT(*) as failed FROM processed_images WHERE success = 0')
            stats['failed'] = cursor.fetchone()['failed']

            cursor = conn.execute('SELECT COUNT(*) as results FROM inbody_results')
            stats['total_results'] = cursor.fetchone()['results']

            return stats
