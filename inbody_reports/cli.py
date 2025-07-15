"""Command-line interface for InBody report generation."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from inbody_reports.report_generator import InBodyReportGenerator


def parse_date(date_string: str) -> datetime:
    """Parse date string in format YYYY-MM-DD."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f'Invalid date format: {date_string}. Use YYYY-MM-DD')


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate beautiful PDF reports from InBody data',
        epilog='Examples:\n'
        '  python -m inbody_reports.cli\n'
        '  python -m inbody_reports.cli --output my_report.pdf\n'
        '  python -m inbody_reports.cli --start-date 2024-01-01 --end-date 2024-12-31\n'
        '  python -m inbody_reports.cli --title "My Fitness Journey 2024"',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--db-path',
        type=str,
        default='inbody_results.db',
        help='Path to the InBody SQLite database (default: inbody_results.db)',
    )

    parser.add_argument(
        '--output', '-o', type=str, help='Output PDF file path (default: auto-generated with timestamp)'
    )

    parser.add_argument('--start-date', type=parse_date, help='Start date for data filtering (format: YYYY-MM-DD)')

    parser.add_argument('--end-date', type=parse_date, help='End date for data filtering (format: YYYY-MM-DD)')

    parser.add_argument('--title', type=str, help='Custom title for the report')

    parser.add_argument('--list-data-range', action='store_true', help='Show the available data range and exit')

    args = parser.parse_args()

    try:
        # Check if database exists
        db_path = Path(args.db_path)
        if not db_path.exists():
            print(f'❌ Error: Database file not found: {db_path}')
            print('Make sure you have processed some InBody images first using the main inbody-to-sqlite tool.')
            sys.exit(1)

        # Initialize report generator
        print('🔧 Initializing report generator...')
        generator = InBodyReportGenerator(str(db_path))

        # Handle list data range option
        if args.list_data_range:
            min_date, max_date = generator.data_processor.get_data_range()
            if min_date and max_date:
                print(f'📅 Available data range: {min_date.strftime("%Y-%m-%d")} to {max_date.strftime("%Y-%m-%d")}')
                total_days = (max_date - min_date).days
                print(f'📊 Total tracking period: {total_days} days')

                # Get total scans
                df = generator.data_processor.get_data_for_timeframe()
                print(f'📈 Total scans: {len(df)}')
            else:
                print('❌ No data available in the database')
            sys.exit(0)

        # Validate date range
        if args.start_date and args.end_date:
            if args.start_date > args.end_date:
                print('❌ Error: Start date cannot be after end date')
                sys.exit(1)

        # Generate report
        print('📊 Generating InBody progress report...')
        if args.start_date or args.end_date:
            print(f'📅 Date range: {args.start_date or "Beginning"} to {args.end_date or "Present"}')

        output_path = generator.generate_report(
            output_path=args.output, start_date=args.start_date, end_date=args.end_date, title=args.title
        )

        print('✅ Report generated successfully!')
        print(f'📄 Output file: {output_path}')
        print(f'📁 File size: {Path(output_path).stat().st_size / 1024:.1f} KB')

        # Show data summary
        df = generator.data_processor.get_data_for_timeframe(args.start_date, args.end_date)
        stats = generator.data_processor.get_summary_stats(df)

        print('\n📈 Report Summary:')
        print(f'  • Total scans included: {stats["total_scans"]}')
        if 'date_range' in stats:
            print(f'  • Tracking period: {stats["date_range"]["days"]} days')
        if 'weight_change' in stats:
            wc = stats['weight_change']
            print(f'  • Weight change: {wc["total_kg"]:+.1f} kg')
        if 'body_fat_change' in stats:
            bc = stats['body_fat_change']
            print(f'  • Body fat change: {bc["total_percent"]:+.1f}%')
        if 'muscle_change' in stats:
            mc = stats['muscle_change']
            print(f'  • Muscle mass change: {mc["total_kg"]:+.1f} kg')

    except ValueError as e:
        print(f'❌ Error: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'💥 Unexpected error: {e}')
        print('Please check your database and try again.')
        sys.exit(1)


if __name__ == '__main__':
    main()
