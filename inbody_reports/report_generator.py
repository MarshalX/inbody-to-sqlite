"""PDF report generation module for InBody reports."""

from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable

from inbody_reports.chart_generator import ChartGenerator
from inbody_reports.data_processor import DataProcessor


class InBodyReportGenerator:
    """Generate comprehensive PDF reports from InBody data."""

    def __init__(self, db_path: str = 'inbody_results.db'):
        """Initialize report generator."""
        self.data_processor = DataProcessor(db_path)
        self.chart_generator = ChartGenerator()
        self.styles = getSampleStyleSheet()

        # Custom styles with optimized spacing
        self.styles.add(
            ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2E86AB'),
                spaceAfter=20,  # Reduced from 30
                alignment=1,  # Center alignment
            )
        )

        self.styles.add(
            ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#A23B72'),
                spaceBefore=15,  # Reduced from 20
                spaceAfter=8,  # Reduced from 12
            )
        )

        self.styles.add(
            ParagraphStyle(
                name='InsightText',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#2C3E50'),
                leftIndent=20,
                spaceBefore=4,  # Reduced from 6
                spaceAfter=4,  # Reduced from 6
            )
        )

    def generate_report(
        self,
        output_path: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        title: Optional[str] = None,
    ) -> str:
        """
        Generate a comprehensive InBody progress report.

        Args:
            output_path: Path for the output PDF file
            start_date: Start date for filtering data
            end_date: End date for filtering data
            title: Custom title for the report

        Returns:
            Path to the generated PDF file
        """
        # Get data for the specified timeframe
        df = self.data_processor.get_data_for_timeframe(start_date, end_date)

        if df.empty:
            raise ValueError('No data available for the specified time range')

        # Generate output filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if start_date and end_date:
                date_range = f'{start_date.strftime("%Y%m%d")}_to_{end_date.strftime("%Y%m%d")}'
                output_path = f'inbody_report_{date_range}_{timestamp}.pdf'
            else:
                output_path = f'inbody_report_{timestamp}.pdf'

        # Create PDF document with optimized margins
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=50,  # Reduced from 72
            leftMargin=50,  # Reduced from 72
            topMargin=50,  # Reduced from 72
            bottomMargin=30,  # Increased from 18 for better footer space
        )

        # Build the story (content)
        story = []

        # Title and summary (page 1)
        story.extend(self._create_title_section(df, title, start_date, end_date))

        # Summary dashboard (try to fit on same page, or start page 2)
        story.extend(self._create_dashboard_section(df))
        story.append(PageBreak())

        # Weight progression and body composition (page 2/3)
        story.extend(self._create_weight_section(df))
        story.extend(self._create_composition_section(df))
        story.append(PageBreak())

        # Health metrics and body metrics (page 3)
        story.extend(self._create_health_metrics_section(df))
        story.extend(self._create_body_metrics_section(df))
        story.append(PageBreak())

        # Control recommendations and advanced composition (page 4)
        story.extend(self._create_control_recommendations_section(df))
        story.extend(self._create_advanced_composition_section(df))
        story.append(PageBreak())

        # Progress comparison and segmental analysis (page 5)
        story.extend(self._create_comparison_section(df))
        story.extend(self._create_segmental_section(df))
        story.append(PageBreak())

        # Insights and recommendations (final page)
        story.extend(self._create_insights_section(df))

        # Build PDF
        doc.build(story)

        return output_path

    def _create_title_section(self, df, title, start_date, end_date) -> list:
        """Create the title section with summary statistics."""
        story = []

        # Main title
        if title:
            story.append(Paragraph(title, self.styles['CustomTitle']))
        else:
            story.append(Paragraph('InBody Progress Report', self.styles['CustomTitle']))

        # Report generation info
        generation_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        story.append(Paragraph(f'Report generated on {generation_date}', self.styles['Normal']))
        story.append(Spacer(1, 15))  # Reduced from 20

        # Data range info
        if start_date or end_date:
            date_range_text = 'Data range: '
            if start_date:
                date_range_text += start_date.strftime('%B %d, %Y')
            else:
                date_range_text += 'Beginning'
            date_range_text += ' to '
            if end_date:
                date_range_text += end_date.strftime('%B %d, %Y')
            else:
                date_range_text += 'Present'
            story.append(Paragraph(date_range_text, self.styles['Normal']))
        else:
            min_date, max_date = self.data_processor.get_data_range()
            if min_date and max_date:
                date_range_text = f'Data range: {min_date.strftime("%B %d, %Y")} to {max_date.strftime("%B %d, %Y")}'
                story.append(Paragraph(date_range_text, self.styles['Normal']))

        story.append(Spacer(1, 20))  # Reduced from 30

        # Summary statistics table
        stats = self.data_processor.get_summary_stats(df)
        if stats:
            story.append(Paragraph('Summary Statistics', self.styles['SectionHeader']))
            summary_data = []

            summary_data.append(['Total Scans', str(stats['total_scans'])])

            if 'date_range' in stats:
                summary_data.append(['Tracking Period', f'{stats["date_range"]["days"]} days'])

            if 'weight_change' in stats:
                wc = stats['weight_change']
                summary_data.append(['Weight Change', f'{wc["total_kg"]:+.1f} kg'])
                summary_data.append(['Weight Range', f'{wc["min_weight"]:.1f} - {wc["max_weight"]:.1f} kg'])

            if 'body_fat_change' in stats:
                bc = stats['body_fat_change']
                summary_data.append(['Body Fat Change', f'{bc["total_percent"]:+.1f}%'])

            if 'muscle_change' in stats:
                mc = stats['muscle_change']
                summary_data.append(['Muscle Mass Change', f'{mc["total_kg"]:+.1f} kg'])

            if 'bmi_change' in stats:
                bc = stats['bmi_change']
                summary_data.append(['BMI Change', f'{bc["total"]:+.1f}'])

            # Create table with optimized width
            table = Table(summary_data, colWidths=[3.2 * inch, 2.3 * inch])  # Slightly wider
            table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8F4FD')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Reduced from 12
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
                    ]
                )
            )

            story.append(table)

        return story

    def _create_dashboard_section(self, df) -> list:
        """Create the dashboard section."""
        story = []
        story.append(Spacer(1, 15))  # Add some space
        story.append(Paragraph('Progress Dashboard', self.styles['SectionHeader']))

        # Generate dashboard chart with larger size
        stats = self.data_processor.get_summary_stats(df)
        dashboard_img = self.chart_generator.create_summary_dashboard(df, stats)

        # Add to story with larger size
        img = Image(dashboard_img, width=7.5 * inch, height=5.5 * inch)  # Adjusted size
        story.append(img)

        return story

    def _create_weight_section(self, df) -> list:
        """Create the weight progression section."""
        story = []

        # Generate weight chart with compact size
        weight_img = self.chart_generator.create_weight_progression_chart(df)

        # Use KeepTogether to ensure title and chart stay together
        weight_content = [
            Paragraph('Weight Progression', self.styles['SectionHeader']),
            Image(weight_img, width=7.5 * inch, height=3.5 * inch),
        ]
        story.append(KeepTogether(weight_content))

        # Add insights with reduced spacing
        stats = self.data_processor.get_summary_stats(df)
        if 'weight_change' in stats:
            wc = stats['weight_change']
            story.append(Spacer(1, 8))  # Reduced spacing
            story.append(Paragraph('Weight Analysis:', self.styles['Normal']))

            change_text = f'Your weight changed by {wc["total_kg"]:+.1f} kg from {wc["start_weight"]} kg to {wc["end_weight"]} kg.'
            story.append(Paragraph(change_text, self.styles['InsightText']))

            range_text = f'During this period, your weight ranged from {wc["min_weight"]} kg to {wc["max_weight"]} kg.'
            story.append(Paragraph(range_text, self.styles['InsightText']))

        story.append(Spacer(1, 10))  # Reduced spacing between sections (was 15)

        return story

    def _create_composition_section(self, df) -> list:
        """Create the body composition section."""
        story = []

        # Generate composition chart with larger size to fill available space
        comp_img = self.chart_generator.create_body_composition_chart(df)

        # Use KeepTogether to ensure title and chart stay together
        composition_content = [
            Paragraph('Body Composition', self.styles['SectionHeader']),
            Image(comp_img, width=7.5 * inch, height=6.0 * inch),
        ]
        story.append(KeepTogether(composition_content))

        # Add insights with minimal spacing
        stats = self.data_processor.get_summary_stats(df)
        story.append(Spacer(1, 8))
        story.append(Paragraph('Body Composition Analysis:', self.styles['Normal']))

        if 'muscle_change' in stats:
            mc = stats['muscle_change']
            muscle_text = f'Muscle mass changed by {mc["total_kg"]:+.1f} kg from {mc["start_muscle"]} kg to {mc["end_muscle"]} kg.'
            story.append(Paragraph(muscle_text, self.styles['InsightText']))

        if 'body_fat_change' in stats:
            bc = stats['body_fat_change']
            fat_text = (
                f'Body fat percentage changed by {bc["total_percent"]:+.1f}% from {bc["start_bf"]}% to {bc["end_bf"]}%.'
            )
            story.append(Paragraph(fat_text, self.styles['InsightText']))

        return story

    def _create_health_metrics_section(self, df) -> list:
        """Create the health metrics section."""
        story = []

        # Generate health metrics chart with compact size
        health_img = self.chart_generator.create_health_metrics_chart(df)

        # Use KeepTogether to ensure title and chart stay together
        health_content = [
            Paragraph('Health Metrics', self.styles['SectionHeader']),
            Image(health_img, width=7.5 * inch, height=4.5 * inch),
        ]
        story.append(KeepTogether(health_content))

        story.append(Spacer(1, 15))  # Spacing between sections

        return story

    def _create_body_metrics_section(self, df) -> list:
        """Create the body metrics section (WHR and total body water)."""
        story = []

        # Generate body metrics chart
        body_metrics_img = self.chart_generator.create_body_metrics_chart(df)

        # Use KeepTogether to ensure title and chart stay together
        body_metrics_content = [
            Paragraph('Body Metrics - WHR & Body Water', self.styles['SectionHeader']),
            Image(body_metrics_img, width=7.5 * inch, height=3.0 * inch),
        ]
        story.append(KeepTogether(body_metrics_content))

        story.append(Spacer(1, 8))
        story.append(
            Paragraph(
                'Waist-Hip Ratio (WHR) is an important indicator of body fat distribution and health risks. '
                'Total body water reflects hydration and overall body composition.',
                self.styles['Normal'],
            )
        )

        story.append(Spacer(1, 15))

        return story

    def _create_control_recommendations_section(self, df) -> list:
        """Create the control recommendations section."""
        story = []

        # Generate control recommendations chart
        control_img = self.chart_generator.create_control_recommendations_chart(df)

        # Use KeepTogether to ensure title and chart stay together
        control_content = [
            Paragraph('InBody Control Recommendations', self.styles['SectionHeader']),
            Image(control_img, width=7.5 * inch, height=5.0 * inch),
        ]
        story.append(KeepTogether(control_content))

        story.append(Spacer(1, 8))
        story.append(
            Paragraph(
                "These are the InBody machine's recommendations for how to improve your body composition. "
                "Positive values suggest gaining muscle or losing fat. Zero indicates you're at the ideal target.",
                self.styles['Normal'],
            )
        )

        story.append(Spacer(1, 15))

        return story

    def _create_advanced_composition_section(self, df) -> list:
        """Create the advanced body composition section."""
        story = []

        # Generate advanced composition chart
        advanced_comp_img = self.chart_generator.create_advanced_composition_chart(df)

        # Use KeepTogether to ensure title and chart stay together
        advanced_comp_content = [
            Paragraph('Advanced Body Composition', self.styles['SectionHeader']),
            Image(advanced_comp_img, width=7.5 * inch, height=3.0 * inch),
        ]
        story.append(KeepTogether(advanced_comp_content))

        story.append(Spacer(1, 8))
        story.append(
            Paragraph(
                'PBF (Percent Body Fat) and Fat-Free Mass provide additional insights into your body composition. '
                'Fat-Free Mass includes muscle, bone, and organs - everything except fat.',
                self.styles['Normal'],
            )
        )

        story.append(Spacer(1, 15))

        return story

    def _create_comparison_section(self, df) -> list:
        """Create the progress comparison section."""
        story = []

        # Generate comparison data and chart
        chart_data = self.data_processor.prepare_chart_data(df)
        if 'comparison' in chart_data and not chart_data['comparison'].empty:
            comp_img = self.chart_generator.create_progress_comparison_chart(chart_data['comparison'])

            # Use KeepTogether to ensure title and chart stay together
            comparison_content = [
                Paragraph('Progress Comparison', self.styles['SectionHeader']),
                Image(comp_img, width=7.5 * inch, height=3.8 * inch),
            ]
            story.append(KeepTogether(comparison_content))
        else:
            story.append(Paragraph('Progress Comparison', self.styles['SectionHeader']))
            story.append(Paragraph('Not enough data for comparison analysis.', self.styles['Normal']))

        return story

    def _create_segmental_section(self, df) -> list:
        """Create the segmental analysis section."""
        story = []

        # Generate segmental data and chart
        chart_data = self.data_processor.prepare_chart_data(df)
        if 'segmental_history' in chart_data and not chart_data['segmental_history'].empty:
            seg_img = self.chart_generator.create_segmental_analysis_chart(chart_data['segmental_history'])

            # Use KeepTogether to ensure title and chart stay together
            segmental_content = [
                Paragraph('Segmental Analysis - Historical Trends', self.styles['SectionHeader']),
                Image(seg_img, width=7.5 * inch, height=6.0 * inch),  # Larger for 2x2 grid
            ]
            story.append(KeepTogether(segmental_content))

            story.append(Spacer(1, 8))  # Reduced spacing
            story.append(
                Paragraph(
                    'This analysis shows the historical development of lean and fat mass across different body parts over time. '
                    'Solid lines represent lean mass, dashed lines represent fat mass. The bottom-right chart shows your latest measurements for comparison.',
                    self.styles['Normal'],
                )
            )
        else:
            story.append(Paragraph('Segmental Analysis - Historical Trends', self.styles['SectionHeader']))
            story.append(Paragraph('No segmental analysis data available.', self.styles['Normal']))

        story.append(Spacer(1, 15))  # Add space before insights

        return story

    def _create_insights_section(self, df) -> list:
        """Create the insights and recommendations section."""
        story = []
        story.append(Paragraph('Insights & Recommendations', self.styles['SectionHeader']))

        # Get insights
        insights = self.data_processor.get_achievement_insights(df)

        for insight in insights:
            story.append(Paragraph(f'• {insight}', self.styles['InsightText']))

        story.append(Spacer(1, 15))  # Reduced spacing

        # Add general recommendations
        story.append(Paragraph('General Recommendations:', self.styles['Normal']))
        story.append(Spacer(1, 8))

        recommendations = [
            'Continue regular InBody scans to track progress consistently',
            'Focus on maintaining muscle mass while managing body fat levels',
            'Consider consulting with a healthcare professional for personalized advice',
            'Combine regular exercise with proper nutrition for optimal results',
            'Monitor trends rather than individual measurements for better insights',
        ]

        for rec in recommendations:
            story.append(Paragraph(f'• {rec}', self.styles['InsightText']))

        # Add footer with reduced spacing
        story.append(Spacer(1, 20))  # Reduced from 30
        story.append(HRFlowable(width='100%', thickness=1, color=colors.gray))
        story.append(Spacer(1, 8))  # Reduced from 12
        footer_text = (
            'This report was automatically generated from your InBody scan data. '
            'Consult with healthcare professionals for medical advice.'
        )
        story.append(Paragraph(footer_text, self.styles['Normal']))

        return story
