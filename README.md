# InBody to SQLite

A Python tool that processes InBody body composition scan images using OpenAI GPT Vision to extract structured data and store it in a local SQLite database. **Now includes a PDF Report Generator for beautiful progress tracking!**

## Features

### Core Features
- **AI-powered text extraction**: Uses OpenAI GPT-4 Vision to analyze InBody scan images
- **Unified data model**: Combines data from different InBody machine models into a single schema
- **Smart caching**: Avoids reprocessing the same images using SHA-256 file hashes
- **SQLite storage**: Stores all extracted data in a local SQLite database
- **Multi-language support**: Handles InBody scans in different languages (English, Polish, etc.)
- **Structured output**: Uses JSON schema validation for consistent data extraction
- **Batch processing**: Process entire folders of images at once
- **Export functionality**: Export results to JSON for analysis

### 🆕 NEW: PDF Report Generator
- **📊 Beautiful Charts**: Generate colorful progress reports with multiple chart types
- **📅 Time Range Filtering**: Create reports for any date range (entire history by default)
- **🎨 Professional Design**: High-quality PDF reports with modern styling
- **💡 Smart Insights**: Automatic analysis of your fitness progress and achievements
- **🔧 Multiple Interfaces**: Both command-line tool and Python API
- **📈 Comprehensive Analysis**: Weight, body composition, health metrics, and segmental analysis

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd inbody-to-sqlite
   ```

2. **Install dependencies using UV**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Configuration

You need an OpenAI API key to use GPT-4 Vision. Get one from [OpenAI Platform](https://platform.openai.com/api-keys).

Create a `.env` file:
```bash
OPENAI_API_KEY=your-api-key-here
```

## Usage

### Core Data Processing

Process a folder of InBody images:
```bash
python -m inbody_to_sqlite /path/to/images
```

### 🆕 PDF Report Generation

Generate beautiful progress reports from your processed data:

```bash
# Generate a complete report
uv run python -m inbody_reports

# Custom report with title and filename
uv run python -m inbody_reports --output "my_fitness_journey.pdf" --title "My Progress Report"

# Report for specific date range
uv run python -m inbody_reports --start-date 2024-01-01 --end-date 2024-12-31

# Check available data
uv run python -m inbody_reports --list-data-range
```

Options:
- `--force`: Reprocess images even if already cached
- `--export`: Export results to JSON after processing
- `--export-only`: Only export existing results, don't process new images

Examples:
```bash
# Process all images in a folder
python -m inbody_to_sqlite ./my_inbody_scans

# Force reprocess all images and export results
python -m inbody_to_sqlite ./my_inbody_scans --force --export

# Export existing results only
python -m inbody_to_sqlite ./my_inbody_scans --export-only
```

### Python API

#### Data Processing
```python
from inbody_to_sqlite.main import InBodyProcessor

# Initialize processor
processor = InBodyProcessor(api_key="your-api-key")

# Process a folder
stats = processor.process_folder("/path/to/images")

# Export results
output_file = processor.export_results()
```

#### 🆕 Report Generation
```python
from inbody_reports import InBodyReportGenerator
from datetime import datetime, timedelta

# Initialize report generator
generator = InBodyReportGenerator('inbody_results.db')

# Generate complete report
report_path = generator.generate_report(
    output_path="progress_report.pdf",
    title="My Fitness Journey"
)

# Generate report for specific time range
six_months_ago = datetime.now() - timedelta(days=180)
recent_report = generator.generate_report(
    start_date=six_months_ago,
    title="Recent Progress"
)
```

## Supported Data Fields

The tool extracts and unifies the following data from InBody scans:

### Basic Information
- **scan_date**: Date and time of the scan
- **height**: Height in cm
- **weight**: Weight in kg
- **age**: Age in years
- **gender**: Gender (Male/Female)

### Body Composition
- **muscle_mass**: Total muscle mass in kg
- **body_fat_mass**: Total body fat mass in kg
- **body_fat_percentage**: Body fat percentage
- **total_body_water**: Total body water in liters
- **fat_free_mass**: Fat-free mass in kg

### Health Metrics
- **bmi**: Body Mass Index
- **bmr**: Basal Metabolic Rate in kcal
- **visceral_fat_level**: Visceral fat level
- **pbf**: Percent body fat
- **whr**: Waist-hip ratio

### Scores & Recommendations
- **inbody_score**: InBody score
- **fitness_score**: Fitness score
- **muscle_control**: Muscle control recommendation in kg
- **fat_control**: Fat control recommendation in kg

### Segmental Analysis
- **segmental**: Body part analysis for arms, trunk, and legs
  - Lean mass for each body part
  - Fat mass for each body part

## Database Schema

The tool creates two main tables:

### `processed_images`
- Tracks which images have been processed
- Stores file hash for cache validation
- Records processing success/failure

### `inbody_results`
- Stores extracted InBody data
- Links to processed images via file hash
- Contains all the structured data fields

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)
- WebP (.webp)

## InBody Models Supported

The tool has been tested with multiple InBody models and handles:
- Different languages (English, Polish, etc.)
- Varying data layouts

## PDF Report Features

The new report generator creates comprehensive PDF reports with:

### 📊 Chart Types
- **Weight Progression**: Timeline with trend analysis
- **Body Composition**: Muscle vs fat mass over time
- **Health Metrics**: BMI, BMR, visceral fat levels
- **Segmental Analysis**: Body part measurements
- **Progress Dashboard**: Key metrics overview
- **Before/After Comparison**: First vs latest scans

### 🎨 Report Sections
1. **Summary Dashboard** - Key progress indicators
2. **Weight Progression** - Detailed weight analysis with trends
3. **Body Composition** - Muscle and fat mass changes
4. **Health Metrics** - BMI, BMR, visceral fat tracking
5. **Progress Comparison** - First vs latest scan analysis
6. **Segmental Analysis** - Body part distribution
7. **Insights & Recommendations** - AI-generated progress insights

### 📈 Sample Results
Your reports will show insights like:
- 📉 Weight decreased by 17.6kg over 773 days
- 💪 Body fat decreased by 14.0% - Great progress!
- ✅ Current BMI is in the healthy range
- 👍 Good tracking consistency - 19 scans over 773 days
- Different measurement units (automatically normalized)
- Missing fields in different models

## Error Handling

- **Caching**: Images are cached by hash to avoid reprocessing
- **Validation**: Pydantic models ensure data consistency
- **Error logging**: Failed extractions are logged with error messages
- **Graceful degradation**: Missing fields are handled as optional

## Examples

### Processing Results

```
🔍 Scanning folder: ./images
📁 Found 5 image files

[1/5] 🔍 Processing inbody_scan_1.jpg...
✅ Successfully processed inbody_scan_1.jpg
   Date: 2023-06-03 06:53:00
   Weight: 93.4kg, Height: 181.0cm
   BMI: 28.5

[2/5] ⏭️  Skipping inbody_scan_2.jpg (already processed)

==================================================
📊 Processing Summary:
   Total files: 5
   Successfully processed: 3
   Failed: 1
   Skipped (cached): 1

📈 Database Statistics:
   Total processed images: 10
   Successful extractions: 9
   Failed extractions: 1
   Total InBody results: 9
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY environment variable is required"**
   - Make sure you've created a `.env` file with your OpenAI API key

2. **"No image files found"**
   - Check that your folder contains supported image formats
   - Verify the folder path is correct

3. **Processing failures**
   - Check your OpenAI API key is valid and has sufficient credits
   - Ensure images are clear and readable InBody scans

### Getting Help

- Check the processing logs for specific error messages
- Verify your OpenAI API key has access to GPT-4 Vision
- Ensure images are high quality and clearly show InBody data
