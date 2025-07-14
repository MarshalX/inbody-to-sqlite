"""Example usage of the InBody to SQLite converter."""

import os
from pathlib import Path

from dotenv import load_dotenv

from inbody_to_sqlite.main import InBodyProcessor


def main():
    """Example usage of the InBody processor."""
    load_dotenv()

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('❌ Error: OPENAI_API_KEY environment variable is required')
        print('Please create a .env file with your OpenAI API key:')
        print('OPENAI_API_KEY=your-api-key-here')
        return

    folder_path = './images'

    if not Path(folder_path).exists():
        print(f"❌ Error: Folder '{folder_path}' does not exist")
        print('Please create the folder and add your InBody scan images')
        return

    processor = InBodyProcessor(api_key=api_key)

    print(f'🚀 Starting to process images in: {folder_path}')
    stats = processor.process_folder(folder_path)

    if stats['processed'] > 0:
        output_file = processor.export_results()
        print(f'📄 Results exported to: {output_file}')


if __name__ == '__main__':
    main()
