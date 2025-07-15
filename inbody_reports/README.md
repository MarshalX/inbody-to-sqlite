# InBody Reports - PDF Report Generator

Generate beautiful, colorful PDF reports from your InBody scan data with charts showing your fitness progress over time.

## Features

- 📊 **Beautiful Charts**: Weight progression, body composition, health metrics, and segmental analysis
- 📅 **Time Range Filtering**: Generate reports for any date range (entire history by default)
- 🎨 **Colorful Design**: Professional-quality PDF reports with multiple chart types
- 💡 **Smart Insights**: Automatic analysis of progress and achievements
- 🔧 **Flexible Options**: Command-line interface and Python API
- 📈 **Multiple Views**: Dashboard, detailed charts, and comparison analysis

## Installation

The reports module is already included in your `inbody-to-sqlite` project. Make sure you have the required dependencies:

```bash
uv sync
```

## Quick Start

### Command Line Interface

Generate a complete report from all your data:

```bash
# Simple report with all data
uv run python -m inbody_reports

# Custom output filename and title
uv run python -m inbody_reports --output "my_fitness_journey.pdf" --title "My 2024 Fitness Progress"

# Report for specific date range
uv run python -m inbody_reports --start-date 2024-01-01 --end-date 2024-12-31

# Check available data range
uv run python -m inbody_reports --list-data-range
```

### Python API

```python
from inbody_reports import InBodyReportGenerator
from datetime import datetime, timedelta

# Initialize generator
generator = InBodyReportGenerator('inbody_results.db')

# Generate complete report
complete_report = generator.generate_report(
    output_path="complete_report.pdf",
    title="Complete InBody Progress Report"
)

# Generate report for specific time range
six_months_ago = datetime.now() - timedelta(days=180)
recent_report = generator.generate_report(
    output_path="recent_progress.pdf",
    start_date=six_months_ago,
    title="Recent 6-Month Progress"
)
```

## CLI Options

| Option              | Description               | Example                   |
|---------------------|---------------------------|---------------------------|
| `--db-path`         | Path to SQLite database   | `--db-path custom.db`     |
| `--output`, `-o`    | Output PDF filename       | `-o my_report.pdf`        |
| `--start-date`      | Start date (YYYY-MM-DD)   | `--start-date 2024-01-01` |
| `--end-date`        | End date (YYYY-MM-DD)     | `--end-date 2024-12-31`   |
| `--title`           | Custom report title       | `--title "My Journey"`    |
| `--list-data-range` | Show available data range | `--list-data-range`       |

## Report Contents

The generated PDF includes:

### 1. Summary Dashboard
- Key metrics overview (weight change, body fat change, muscle change)
- Progress indicators
- Tracking period summary

### 2. Weight Progression
- Weight over time with trend line
- Min/max weight highlights
- Weight change analysis

### 3. Body Composition
- Muscle mass VS body fat mass over time
- Body fat percentage trends
- Healthy range indicators

### 4. Health Metrics
- BMI progression with healthy ranges
- Basal Metabolic Rate (BMR) trends
- Visceral fat level tracking
- InBody score progression

### 5. Progress Comparison
- First scan vs latest scan comparison
- Change visualization for all metrics
- Percentage changes

### 6. Segmental Analysis
- Body part measurements (latest scan)
- Lean mass distribution
- Fat mass distribution

### 7. Insights & Recommendations
- Automated progress insights
- Achievement highlights
- General fitness recommendations

## Chart Types

- **Line Charts**: Time series data (weight, muscle mass, body fat)
- **Bar Charts**: Segmental analysis and comparisons
- **Trend Lines**: Progress direction indicators
- **Color-coded Ranges**: Health zones and targets
- **Scatter Plots**: Min/max highlights

## Data Requirements

- At least 1 InBody scan in your database
- For meaningful insights, 2+ scans are recommended
- Time-based analysis works best with 3+ scans over time

## Examples

### Example 1: Complete Report
```bash
uv run python -m inbody_reports --title "Complete Fitness Journey"
```

### Example 2: Recent Progress
```bash
uv run python -m inbody_reports \
  --start-date 2024-01-01 \
  --title "2024 Progress" \
  --output "2024_progress.pdf"
```

### Example 3: Python Automation
```python
from inbody_reports import InBodyReportGenerator
from datetime import datetime

generator = InBodyReportGenerator()

# Check data availability
min_date, max_date = generator.data_processor.get_data_range()
print(f"Data available: {min_date} to {max_date}")

# Generate report
report_path = generator.generate_report(
    title="Automated Monthly Report",
    output_path=f"monthly_report_{datetime.now().strftime('%Y_%m')}.pdf"
)

print(f"Report generated: {report_path}")
```

## File Structure

```
inbody_reports/
├── __init__.py           # Module exports
├── __main__.py           # CLI entry point
├── cli.py                # Command-line interface
├── data_processor.py     # Database operations and data analysis
├── chart_generator.py    # Chart creation with matplotlib
├── report_generator.py   # PDF generation with reportlab
└── README.md            # This documentation
```

## Dependencies

- **matplotlib**: Chart generation
- **reportlab**: PDF creation
- **pandas**: Data manipulation
- **seaborn**: Enhanced chart styling
- **inbody-to-sqlite**: Core database functionality

## Output Quality

- **High DPI**: 300 DPI charts for crisp printing
- **Professional Layout**: Multi-page structured reports
- **Color Consistency**: Branded color scheme throughout
- **Font Optimization**: Clear, readable typography

## Troubleshooting

### No Data Available
- Ensure you've processed InBody images first: `python -m inbody_to_sqlite /path/to/images`
- Check data range: `uv run python -m inbody_reports --list-data-range`

### Font Warnings
- Unicode emoji warnings are cosmetic and don't affect functionality
- Charts will still render correctly with fallback characters

### Large File Sizes
- PDF files are typically 1-3MB due to high-quality charts
- This ensures professional print quality

## Advanced Usage

### Custom Data Processing
```python
from inbody_reports import DataProcessor

processor = DataProcessor('inbody_results.db')
df = processor.get_data_for_timeframe()
stats = processor.get_summary_stats(df)
insights = processor.get_achievement_insights(df)
```

### Custom Charts
```python
from inbody_reports import ChartGenerator

generator = ChartGenerator(dpi=300)
weight_chart = generator.create_weight_progression_chart(df)
# weight_chart is a BytesIO object with PNG data
```

This module transforms your InBody data into actionable insights through beautiful, comprehensive PDF reports! 🎉
