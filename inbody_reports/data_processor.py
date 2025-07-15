"""Data processing module for InBody reports."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from inbody_to_sqlite.database import InBodyDatabase


class DataProcessor:
    """Process InBody data for report generation."""

    def __init__(self, db_path: str = 'inbody_results.db'):
        """Initialize with database path."""
        self.db_path = Path(db_path)
        self.db = InBodyDatabase(str(db_path))

    def get_data_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get the date range of available data."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT MIN(scan_date) as min_date, MAX(scan_date) as max_date 
                FROM inbody_results
                ORDER BY scan_date
            """)
            result = cursor.fetchone()

            if result and result['min_date'] and result['max_date']:
                # Handle different date formats from database
                min_date_val = result['min_date']
                max_date_val = result['max_date']

                # Convert based on data type
                if isinstance(min_date_val, int):
                    # Unix timestamp in milliseconds
                    min_date = datetime.fromtimestamp(min_date_val / 1000)
                    max_date = datetime.fromtimestamp(max_date_val / 1000)
                elif isinstance(min_date_val, str):
                    # ISO format string
                    min_date = datetime.fromisoformat(min_date_val)
                    max_date = datetime.fromisoformat(max_date_val)
                elif hasattr(min_date_val, 'isoformat'):
                    # Already datetime objects
                    min_date = min_date_val
                    max_date = max_date_val
                else:
                    # Try to parse as string
                    min_date = datetime.fromisoformat(str(min_date_val))
                    max_date = datetime.fromisoformat(str(max_date_val))

                return min_date, max_date

            return None, None

    def get_data_for_timeframe(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get InBody data for specified timeframe.

        Args:
            start_date: Start date for filtering (None = no limit)
            end_date: End date for filtering (None = no limit)

        Returns:
            DataFrame with InBody results
        """
        with self.db.get_connection() as conn:
            query = """
                SELECT * FROM inbody_results 
                WHERE 1=1
            """
            params = []

            if start_date:
                query += ' AND scan_date >= ?'
                params.append(start_date.isoformat())

            if end_date:
                query += ' AND scan_date <= ?'
                params.append(end_date.isoformat())

            query += ' ORDER BY scan_date ASC'

            df = pd.read_sql_query(query, conn, params=params)

            # Convert scan_date to datetime (handle both timestamps and ISO strings)
            if not df.empty:
                # Check if scan_date contains integers (timestamps)
                is_int_dtype = df['scan_date'].dtype in ['int64', 'int32']
                is_object_with_ints = df['scan_date'].dtype == 'object' and all(
                    isinstance(x, int) for x in df['scan_date'].dropna()
                )

                if is_int_dtype or is_object_with_ints:
                    # Unix timestamp in milliseconds
                    df['scan_date'] = pd.to_datetime(df['scan_date'], unit='ms')
                else:
                    # ISO format strings or other formats
                    df['scan_date'] = pd.to_datetime(df['scan_date'])

            return df

    def get_summary_stats(self, df: pd.DataFrame) -> dict[str, Any]:
        """Get summary statistics for the dataset."""
        if df.empty:
            return {}

        # Calculate basic stats
        stats = {
            'total_scans': len(df),
            'date_range': {
                'start': df['scan_date'].min(),
                'end': df['scan_date'].max(),
                'days': (df['scan_date'].max() - df['scan_date'].min()).days,
            },
        }

        # Weight changes
        if len(df) > 1:
            weight_change = df['weight'].iloc[-1] - df['weight'].iloc[0]
            stats['weight_change'] = {
                'total_kg': round(weight_change, 1),
                'start_weight': round(df['weight'].iloc[0], 1),
                'end_weight': round(df['weight'].iloc[-1], 1),
                'min_weight': round(df['weight'].min(), 1),
                'max_weight': round(df['weight'].max(), 1),
            }

            # Body composition changes
            if df['body_fat_percentage'].notna().sum() > 1:
                bf_change = df['body_fat_percentage'].iloc[-1] - df['body_fat_percentage'].iloc[0]
                stats['body_fat_change'] = {
                    'total_percent': round(bf_change, 1),
                    'start_bf': round(df['body_fat_percentage'].iloc[0], 1),
                    'end_bf': round(df['body_fat_percentage'].iloc[-1], 1),
                }

            if df['muscle_mass'].notna().sum() > 1:
                muscle_change = df['muscle_mass'].iloc[-1] - df['muscle_mass'].iloc[0]
                stats['muscle_change'] = {
                    'total_kg': round(muscle_change, 1),
                    'start_muscle': round(df['muscle_mass'].iloc[0], 1),
                    'end_muscle': round(df['muscle_mass'].iloc[-1], 1),
                }

            # BMI changes
            if df['bmi'].notna().sum() > 1:
                bmi_change = df['bmi'].iloc[-1] - df['bmi'].iloc[0]
                stats['bmi_change'] = {
                    'total': round(bmi_change, 1),
                    'start_bmi': round(df['bmi'].iloc[0], 1),
                    'end_bmi': round(df['bmi'].iloc[-1], 1),
                }

        return stats

    def prepare_chart_data(self, df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Prepare data for different chart types."""
        chart_data = {}

        # Time series data for weight, muscle mass, body fat, and additional metrics
        time_series_cols = [
            'scan_date',
            'weight',
            'muscle_mass',
            'body_fat_mass',
            'body_fat_percentage',
            'bmi',
            'bmr',
            'visceral_fat_level',
            'total_body_water',
            'fat_free_mass',
            'body_score',
            'muscle_control',
            'fat_control',
            'whr',
            'pbf',
        ]
        chart_data['time_series'] = df[time_series_cols].dropna(subset=['scan_date'])

        # Historical segmental analysis data
        if not df.empty:
            # Historical segmental trends (all scans over time)
            segmental_cols = [
                'scan_date',
                'right_arm_lean',
                'left_arm_lean',
                'trunk_lean',
                'right_leg_lean',
                'left_leg_lean',
                'right_arm_fat',
                'left_arm_fat',
                'trunk_fat',
                'right_leg_fat',
                'left_leg_fat',
            ]

            segmental_history = df[segmental_cols].copy()
            # Only include rows that have at least some segmental data
            segmental_mask = segmental_history[segmental_cols[1:]].notna().any(axis=1)
            segmental_history = segmental_history[segmental_mask]

            chart_data['segmental_history'] = segmental_history

            # Latest scan segmental for current breakdown
            if not segmental_history.empty:
                latest_scan = segmental_history.iloc[-1]
                segmental_data = []

                # Lean mass segmental
                lean_parts = ['right_arm_lean', 'left_arm_lean', 'trunk_lean', 'right_leg_lean', 'left_leg_lean']
                for part in lean_parts:
                    if pd.notna(latest_scan[part]):
                        segmental_data.append(
                            {
                                'body_part': part.replace('_lean', '').replace('_', ' ').title(),
                                'measurement_type': 'Lean Mass',
                                'value': latest_scan[part],
                            }
                        )

                # Fat mass segmental
                fat_parts = ['right_arm_fat', 'left_arm_fat', 'trunk_fat', 'right_leg_fat', 'left_leg_fat']
                for part in fat_parts:
                    if pd.notna(latest_scan[part]):
                        segmental_data.append(
                            {
                                'body_part': part.replace('_fat', '').replace('_', ' ').title(),
                                'measurement_type': 'Fat Mass',
                                'value': latest_scan[part],
                            }
                        )

                chart_data['segmental'] = pd.DataFrame(segmental_data)
            else:
                chart_data['segmental'] = pd.DataFrame()

        # Body composition comparison (first vs last)
        if len(df) > 1:
            first_scan = df.iloc[0]
            last_scan = df.iloc[-1]

            composition_data = []
            metrics = {
                'Weight': 'weight',
                'Muscle Mass': 'muscle_mass',
                'Body Fat Mass': 'body_fat_mass',
                'Body Fat %': 'body_fat_percentage',
                'BMI': 'bmi',
                'Visceral Fat': 'visceral_fat_level',
            }

            for metric_name, metric_col in metrics.items():
                if pd.notna(first_scan[metric_col]) and pd.notna(last_scan[metric_col]):
                    composition_data.append(
                        {
                            'metric': metric_name,
                            'first_scan': first_scan[metric_col],
                            'last_scan': last_scan[metric_col],
                            'change': last_scan[metric_col] - first_scan[metric_col],
                            'change_percent': (
                                (last_scan[metric_col] - first_scan[metric_col]) / first_scan[metric_col]
                            )
                            * 100,
                        }
                    )

            chart_data['comparison'] = pd.DataFrame(composition_data)

        return chart_data

    def get_achievement_insights(self, df: pd.DataFrame) -> list[str]:
        """Generate insights and achievements based on the data."""
        insights = []

        if df.empty or len(df) < 2:
            return ['Not enough data to generate insights. Need at least 2 scans.']

        stats = self.get_summary_stats(df)

        # Weight insights
        if 'weight_change' in stats:
            weight_change = stats['weight_change']['total_kg']
            if weight_change > 0:
                insights.append(f'Weight increased by {abs(weight_change)}kg over {stats["date_range"]["days"]} days')
            elif weight_change < -0.5:
                insights.append(f'Weight decreased by {abs(weight_change)}kg over {stats["date_range"]["days"]} days')
            else:
                insights.append(
                    f'Weight remained stable (±{abs(weight_change)}kg) over {stats["date_range"]["days"]} days'
                )

        # Body fat insights
        if 'body_fat_change' in stats:
            bf_change = stats['body_fat_change']['total_percent']
            if bf_change < -1:
                insights.append(f'Body fat decreased by {abs(bf_change):.1f}% - Great progress!')
            elif bf_change > 1:
                insights.append(f'Body fat increased by {bf_change:.1f}%')

        # Muscle mass insights
        if 'muscle_change' in stats:
            muscle_change = stats['muscle_change']['total_kg']
            if muscle_change > 0.5:
                insights.append(f'Muscle mass increased by {muscle_change:.1f}kg - Excellent!')
            elif muscle_change < -0.5:
                insights.append(f'Muscle mass decreased by {abs(muscle_change):.1f}kg')

        # BMI insights
        if 'bmi_change' in stats:
            current_bmi = stats['bmi_change']['end_bmi']
            if current_bmi < 18.5:
                insights.append('Current BMI indicates underweight')
            elif 18.5 <= current_bmi < 25:
                insights.append('Current BMI is in the healthy range')
            elif 25 <= current_bmi < 30:
                insights.append('Current BMI indicates overweight')
            else:
                insights.append('Current BMI indicates obesity')

        # Consistency insights
        scan_frequency = len(df) / max(1, stats['date_range']['days'] / 30)  # scans per month
        if scan_frequency >= 1:
            insights.append(f'Excellent tracking consistency - {len(df)} scans over {stats["date_range"]["days"]} days')
        elif scan_frequency >= 0.5:
            insights.append(f'Good tracking consistency - {len(df)} scans over {stats["date_range"]["days"]} days')

        return insights
