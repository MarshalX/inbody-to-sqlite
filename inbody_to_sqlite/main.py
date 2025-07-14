"""Main application logic for processing InBody scan images."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from inbody_to_sqlite.database import InBodyDatabase
from inbody_to_sqlite.image_processor import InBodyImageProcessor
from inbody_to_sqlite.models import ProcessedImage


class InBodyProcessor:
    """Main processor for InBody scan images."""

    def __init__(self, db_path: str = 'inbody_results.db', api_key: Optional[str] = None):
        """Initialize the processor with database and image processor."""
        self.db = InBodyDatabase(db_path)
        self.processor = InBodyImageProcessor(api_key)

    def find_image_files(self, folder_path: Path) -> list[Path]:
        """Find all image files in the specified folder."""
        if not folder_path.exists():
            raise FileNotFoundError(f'Folder not found: {folder_path}')

        if not folder_path.is_dir():
            raise ValueError(f'Path is not a directory: {folder_path}')

        supported_extensions = self.processor.get_supported_extensions()
        image_files = []

        for ext in supported_extensions:
            # Search for files with each supported extension (case insensitive)
            image_files.extend(folder_path.glob(f'*{ext}'))
            image_files.extend(folder_path.glob(f'*{ext.upper()}'))

        return sorted(list(set(image_files)))  # Remove duplicates and sort

    def process_single_image(self, image_path: Path, force_reprocess: bool = False) -> bool:
        """
        Process a single image file.

        Args:
            image_path: Path to the image file
            force_reprocess: If True, reprocess even if already cached

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate image hash for caching
            file_hash = self.processor.calculate_image_hash(image_path)

            # Check if already processed (unless forced)
            if not force_reprocess and self.db.is_image_processed(file_hash):
                print(f'⏭️  Skipping {image_path.name} (already processed)')
                return True

            print(f'🔍 Processing {image_path.name}...')

            # Process the image
            result, raw_response = self.processor.process_image(image_path)

            # Record the processing attempt
            processed_image = ProcessedImage(
                file_path=str(image_path),
                file_hash=file_hash,
                processed_at=datetime.now(),
                success=result is not None,
                error_message=raw_response if result is None else None,
            )

            self.db.record_processed_image(processed_image)

            if result:
                # Save the extracted data
                self.db.save_inbody_result(result, file_hash)
                print(f'✅ Successfully processed {image_path.name}')
                print(f'   Date: {result.scan_date}')
                print(f'   Weight: {result.weight}kg, Height: {result.height}cm')
                if result.bmi:
                    print(f'   BMI: {result.bmi}')
                return True
            else:
                print(f'❌ Failed to process {image_path.name}')
                print(f'   Error: {raw_response}')
                return False

        except Exception as e:
            print(f'💥 Exception processing {image_path.name}: {e}')
            return False

    def process_folder(self, folder_path: str, force_reprocess: bool = False) -> dict:
        """
        Process all images in a folder.

        Args:
            folder_path: Path to folder containing images
            force_reprocess: If True, reprocess even cached images

        Returns:
            dict: Processing statistics
        """
        folder = Path(folder_path)

        print(f'🔍 Scanning folder: {folder}')

        # Find all image files
        image_files = self.find_image_files(folder)

        if not image_files:
            print('❌ No image files found in the specified folder')
            return {'total': 0, 'processed': 0, 'failed': 0, 'skipped': 0}

        print(f'📁 Found {len(image_files)} image files')

        # Process each image
        stats = {'total': len(image_files), 'processed': 0, 'failed': 0, 'skipped': 0}

        for i, image_path in enumerate(image_files, 1):
            print(f'\n[{i}/{len(image_files)}] ', end='')

            # Check if already processed
            file_hash = self.processor.calculate_image_hash(image_path)
            if not force_reprocess and self.db.is_image_processed(file_hash):
                print(f'⏭️  Skipping {image_path.name} (already processed)')
                stats['skipped'] += 1
                continue

            # Process the image
            success = self.process_single_image(image_path, force_reprocess)

            if success:
                stats['processed'] += 1
            else:
                stats['failed'] += 1

        # Print summary
        print(f'\n{"=" * 50}')
        print('📊 Processing Summary:')
        print(f'   Total files: {stats["total"]}')
        print(f'   Successfully processed: {stats["processed"]}')
        print(f'   Failed: {stats["failed"]}')
        print(f'   Skipped (cached): {stats["skipped"]}')

        # Get database stats
        db_stats = self.db.get_processing_stats()
        print('\n📈 Database Statistics:')
        print(f'   Total processed images: {db_stats["total_processed"]}')
        print(f'   Successful extractions: {db_stats["successful"]}')
        print(f'   Failed extractions: {db_stats["failed"]}')
        print(f'   Total InBody results: {db_stats["total_results"]}')

        return stats

    def export_results(self, output_file: Optional[str] = None) -> str:
        """
        Export all results to a JSON file.

        Args:
            output_file: Output file path. If None, generates a timestamped filename.

        Returns:
            str: Path to the exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'inbody_results_{timestamp}.json'

        results = self.db.get_all_results()

        # Convert datetime objects to strings for JSON serialization
        for result in results:
            if result.get('scan_date') and hasattr(result['scan_date'], 'isoformat'):
                result['scan_date'] = result['scan_date'].isoformat()
            if result.get('processed_at') and hasattr(result['processed_at'], 'isoformat'):
                result['processed_at'] = result['processed_at'].isoformat()
            if result.get('created_at') and hasattr(result['created_at'], 'isoformat'):
                result['created_at'] = result['created_at'].isoformat()

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f'📄 Results exported to: {output_file}')
        return output_file


def main():
    """Main entry point for the CLI application."""
    # Load environment variables
    load_dotenv()

    # Check for required arguments
    if len(sys.argv) < 2:
        print('Usage: python -m inbody_to_sqlite <folder_path> [--force] [--export]')
        print('       python -m inbody_to_sqlite <folder_path> --export-only')
        print('')
        print('Options:')
        print('  --force        Reprocess images even if already cached')
        print('  --export       Export results to JSON after processing')
        print("  --export-only  Only export existing results, don't process new images")
        sys.exit(1)

    folder_path = sys.argv[1]
    force_reprocess = '--force' in sys.argv
    export_results = '--export' in sys.argv
    export_only = '--export-only' in sys.argv

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key and not export_only:
        print('❌ Error: OPENAI_API_KEY environment variable is required')
        print('Please set your OpenAI API key:')
        print("export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)

    try:
        processor = InBodyProcessor(api_key=api_key)

        if export_only:
            output_file = processor.export_results()
            print(f'✅ Export completed: {output_file}')
        else:
            processor.process_folder(folder_path, force_reprocess)

            if export_results:
                processor.export_results()

    except KeyboardInterrupt:
        print('\n\n⏹️  Processing interrupted by user')
        sys.exit(1)
    except Exception as e:
        print(f'\n💥 Fatal error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
