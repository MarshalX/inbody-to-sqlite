"""Chart generation module for InBody reports."""

import io

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Set modern color palette and style
try:
    plt.style.use('seaborn-v0_8')
except OSError:
    # Fallback to default style if seaborn style is not available
    plt.style.use('default')
sns.set_palette('husl')


class ChartGenerator:
    """Generate beautiful charts for InBody data."""

    def __init__(self, style: str = 'default', dpi: int = 300):
        """Initialize chart generator with styling options."""
        try:
            plt.style.use(style)
        except OSError:
            # Fallback to default style if requested style is not available
            plt.style.use('default')
        self.dpi = dpi
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'accent': '#F18F01',
            'success': '#C73E1D',
            'info': '#8E44AD',
            'light': '#BDC3C7',
            'dark': '#2C3E50',
        }

        # Configure matplotlib for better quality
        plt.rcParams.update(
            {
                'figure.dpi': self.dpi,
                'savefig.dpi': self.dpi,
                'font.size': 10,
                'axes.titlesize': 14,
                'axes.labelsize': 12,
                'xtick.labelsize': 10,
                'ytick.labelsize': 10,
                'legend.fontsize': 10,
                'figure.titlesize': 16,
            }
        )

    def create_weight_progression_chart(self, df: pd.DataFrame) -> io.BytesIO:
        """Create weight progression over time chart."""
        fig, ax = plt.subplots(figsize=(12, 6))

        # Filter data with weight values
        weight_data = df[df['weight'].notna()].copy()

        if weight_data.empty:
            ax.text(0.5, 0.5, 'No weight data available', transform=ax.transAxes, ha='center', va='center', fontsize=14)
            ax.set_title('Weight Progression Over Time')
        else:
            # Main weight line
            ax.plot(
                weight_data['scan_date'],
                weight_data['weight'],
                color=self.colors['primary'],
                linewidth=3,
                marker='o',
                markersize=6,
                label='Weight (kg)',
            )

            # Add trend line
            if len(weight_data) > 2:
                z = np.polyfit(mdates.date2num(weight_data['scan_date']), weight_data['weight'], 1)
                p = np.poly1d(z)
                ax.plot(
                    weight_data['scan_date'],
                    p(mdates.date2num(weight_data['scan_date'])),
                    '--',
                    color=self.colors['accent'],
                    alpha=0.8,
                    linewidth=2,
                    label='Trend',
                )

            # Highlight min and max
            min_weight_idx = weight_data['weight'].idxmin()
            max_weight_idx = weight_data['weight'].idxmax()

            ax.scatter(
                weight_data.loc[min_weight_idx, 'scan_date'],
                weight_data.loc[min_weight_idx, 'weight'],
                color=self.colors['success'],
                s=100,
                zorder=5,
                label=f'Min: {weight_data.loc[min_weight_idx, "weight"]:.1f}kg',
            )

            ax.scatter(
                weight_data.loc[max_weight_idx, 'scan_date'],
                weight_data.loc[max_weight_idx, 'weight'],
                color=self.colors['secondary'],
                s=100,
                zorder=5,
                label=f'Max: {weight_data.loc[max_weight_idx, "weight"]:.1f}kg',
            )

            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            plt.xticks(rotation=45)

            ax.set_ylabel('Weight (kg)')
            ax.legend()
            ax.grid(True, alpha=0.3)

        ax.set_title('Weight Progression Over Time', fontweight='bold', pad=20)
        plt.tight_layout()

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def create_body_composition_chart(self, df: pd.DataFrame) -> io.BytesIO:
        """Create body composition chart showing muscle vs fat over time."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Filter data with composition values
        comp_data = df[(df['muscle_mass'].notna()) | (df['body_fat_mass'].notna())].copy()

        if comp_data.empty:
            ax1.text(
                0.5,
                0.5,
                'No body composition data available',
                transform=ax1.transAxes,
                ha='center',
                va='center',
                fontsize=14,
            )
        else:
            # Muscle mass and body fat mass
            if comp_data['muscle_mass'].notna().sum() > 0:
                ax1.plot(
                    comp_data['scan_date'],
                    comp_data['muscle_mass'],
                    color=self.colors['success'],
                    linewidth=3,
                    marker='o',
                    markersize=6,
                    label='Muscle Mass (kg)',
                )

            if comp_data['body_fat_mass'].notna().sum() > 0:
                ax1.plot(
                    comp_data['scan_date'],
                    comp_data['body_fat_mass'],
                    color=self.colors['secondary'],
                    linewidth=3,
                    marker='s',
                    markersize=6,
                    label='Body Fat Mass (kg)',
                )

            ax1.set_ylabel('Mass (kg)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_title('Body Composition - Mass', fontweight='bold')

            # Body fat percentage
            if comp_data['body_fat_percentage'].notna().sum() > 0:
                ax2.plot(
                    comp_data['scan_date'],
                    comp_data['body_fat_percentage'],
                    color=self.colors['accent'],
                    linewidth=3,
                    marker='^',
                    markersize=6,
                    label='Body Fat %',
                )

                # Add healthy range shading (example ranges)
                ax2.axhspan(10, 20, alpha=0.2, color=self.colors['success'], label='Healthy Range (example)')

            # Format x-axis for both subplots
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

            ax2.set_ylabel('Body Fat (%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.set_title('Body Fat Percentage', fontweight='bold')

        plt.tight_layout()

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def create_health_metrics_chart(self, df: pd.DataFrame) -> io.BytesIO:
        """Create health metrics chart (BMI, BMR, Visceral Fat)."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        metrics_data = df[['scan_date', 'bmi', 'bmr', 'visceral_fat_level', 'body_score']].copy()

        # BMI Chart
        bmi_data = metrics_data[metrics_data['bmi'].notna()]
        if not bmi_data.empty:
            ax1.plot(
                bmi_data['scan_date'],
                bmi_data['bmi'],
                color=self.colors['primary'],
                linewidth=3,
                marker='o',
                markersize=6,
            )

            # BMI ranges
            ax1.axhspan(18.5, 25, alpha=0.2, color=self.colors['success'], label='Normal')
            ax1.axhspan(25, 30, alpha=0.2, color=self.colors['accent'], label='Overweight')
            ax1.axhspan(30, 40, alpha=0.2, color=self.colors['secondary'], label='Obese')

            ax1.set_ylabel('BMI')
            ax1.legend()
        ax1.set_title('Body Mass Index', fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # BMR Chart
        bmr_data = metrics_data[metrics_data['bmr'].notna()]
        if not bmr_data.empty:
            ax2.plot(
                bmr_data['scan_date'],
                bmr_data['bmr'],
                color=self.colors['accent'],
                linewidth=3,
                marker='s',
                markersize=6,
            )
            ax2.set_ylabel('BMR (kcal)')
        ax2.set_title('Basal Metabolic Rate', fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # Visceral Fat Chart
        vf_data = metrics_data[metrics_data['visceral_fat_level'].notna()]
        if not vf_data.empty:
            ax3.plot(
                vf_data['scan_date'],
                vf_data['visceral_fat_level'],
                color=self.colors['secondary'],
                linewidth=3,
                marker='^',
                markersize=6,
            )

            # Healthy range for visceral fat
            ax3.axhspan(0, 10, alpha=0.2, color=self.colors['success'], label='Healthy')
            ax3.axhspan(10, 15, alpha=0.2, color=self.colors['accent'], label='High')
            ax3.axhspan(15, 30, alpha=0.2, color=self.colors['secondary'], label='Very High')

            ax3.set_ylabel('Visceral Fat Level')
            ax3.legend()
        ax3.set_title('Visceral Fat Level', fontweight='bold')
        ax3.grid(True, alpha=0.3)

        # Body Score Chart
        score_data = metrics_data[metrics_data['body_score'].notna()]
        if not score_data.empty:
            ax4.plot(
                score_data['scan_date'],
                score_data['body_score'],
                color=self.colors['info'],
                linewidth=3,
                marker='D',
                markersize=6,
            )
            ax4.set_ylabel('Body Score')
        ax4.set_title('InBody Score', fontweight='bold')
        ax4.grid(True, alpha=0.3)

        # Format x-axis for all subplots
        for ax in [ax1, ax2, ax3, ax4]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # Show every 3 months
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def create_segmental_analysis_chart(self, segmental_history_df: pd.DataFrame) -> io.BytesIO:
        """Create comprehensive historical segmental analysis chart."""
        if segmental_history_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(
                0.5,
                0.5,
                'No segmental analysis data available',
                transform=ax.transAxes,
                ha='center',
                va='center',
                fontsize=14,
            )
            ax.set_title('Segmental Analysis - Historical Trends')
            plt.tight_layout()
        else:
            # Create a comprehensive 2x2 grid for different body part groups
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

            # Set main title for the whole figure with more space
            fig.suptitle('Segmental Analysis - Historical Trends by Body Part', fontsize=16, fontweight='bold', y=0.96)

            # 1. Arms Trend (Top Left)
            self._plot_body_part_trend(
                ax1,
                segmental_history_df,
                ['right_arm_lean', 'left_arm_lean', 'right_arm_fat', 'left_arm_fat'],
                'Arms Development',
                ['Right Arm Lean', 'Left Arm Lean', 'Right Arm Fat', 'Left Arm Fat'],
            )

            # 2. Legs Trend (Top Right)
            self._plot_body_part_trend(
                ax2,
                segmental_history_df,
                ['right_leg_lean', 'left_leg_lean', 'right_leg_fat', 'left_leg_fat'],
                'Legs Development',
                ['Right Leg Lean', 'Left Leg Lean', 'Right Leg Fat', 'Left Leg Fat'],
            )

            # 3. Trunk Trend (Bottom Left)
            self._plot_body_part_trend(
                ax3, segmental_history_df, ['trunk_lean', 'trunk_fat'], 'Trunk Development', ['Trunk Lean', 'Trunk Fat']
            )

            # 4. Body Part Comparison (Bottom Right) - Latest values
            self._plot_latest_segmental_comparison(ax4, segmental_history_df)

        # Improve spacing with better layout adjustments
        plt.tight_layout()
        plt.subplots_adjust(top=0.90, hspace=0.35, wspace=0.25)  # More space between elements

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def _plot_body_part_trend(self, ax, df: pd.DataFrame, columns: list[str], title: str, labels: list[str]):
        """Plot trend lines for specific body parts."""
        colors_cycle = [self.colors['primary'], self.colors['accent'], self.colors['secondary'], self.colors['info']]

        for i, (col, label) in enumerate(zip(columns, labels)):
            if col in df.columns and df[col].notna().any():
                # Filter out NaN values for cleaner lines
                clean_data = df[['scan_date', col]].dropna()
                if not clean_data.empty:
                    color = colors_cycle[i % len(colors_cycle)]
                    alpha = 0.8 if 'lean' in col.lower() else 0.6
                    linewidth = 2.5 if 'lean' in col.lower() else 2
                    linestyle = '-' if 'lean' in col.lower() else '--'

                    ax.plot(
                        clean_data['scan_date'],
                        clean_data[col],
                        marker='o',
                        linewidth=linewidth,
                        linestyle=linestyle,
                        color=color,
                        alpha=alpha,
                        label=label,
                        markersize=4,
                    )

        ax.set_title(title, fontweight='bold', pad=20)  # Increased padding
        ax.set_ylabel('Mass (kg)')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc='best')

        # Format dates on x-axis
        if not df.empty:
            dates = pd.to_datetime(df['scan_date'])
            if len(dates) > 6:
                ax.tick_params(axis='x', rotation=45)
                # Show fewer x-axis labels for readability
                for label in ax.get_xticklabels()[:: max(1, len(dates) // 6)]:
                    label.set_visible(True)

    def _plot_latest_segmental_comparison(self, ax, df: pd.DataFrame):
        """Plot comparison of latest segmental measurements."""
        if df.empty:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, ha='center', va='center')
            ax.set_title('Latest Measurements Comparison')
            return

        latest = df.iloc[-1]

        # Prepare data for grouped bar chart
        body_parts = ['Right Arm', 'Left Arm', 'Trunk', 'Right Leg', 'Left Leg']
        lean_values = []
        fat_values = []

        lean_cols = ['right_arm_lean', 'left_arm_lean', 'trunk_lean', 'right_leg_lean', 'left_leg_lean']
        fat_cols = ['right_arm_fat', 'left_arm_fat', 'trunk_fat', 'right_leg_fat', 'left_leg_fat']

        for lean_col, fat_col in zip(lean_cols, fat_cols):
            lean_values.append(latest[lean_col] if pd.notna(latest[lean_col]) else 0)
            fat_values.append(latest[fat_col] if pd.notna(latest[fat_col]) else 0)

        # Create grouped bar chart
        x = range(len(body_parts))
        width = 0.35

        bars1 = ax.bar(
            [i - width / 2 for i in x], lean_values, width, label='Lean Mass', color=self.colors['success'], alpha=0.8
        )
        bars2 = ax.bar(
            [i + width / 2 for i in x], fat_values, width, label='Fat Mass', color=self.colors['secondary'], alpha=0.8
        )

        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.1,
                    f'{height:.1f}',
                    ha='center',
                    va='bottom',
                    fontsize=8,
                )

        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.02,
                    f'{height:.1f}',
                    ha='center',
                    va='bottom',
                    fontsize=8,
                )

        ax.set_title('Latest Scan - Body Part Comparison', fontweight='bold', pad=20)  # Increased padding
        ax.set_ylabel('Mass (kg)')
        ax.set_xlabel('Body Parts')
        ax.set_xticks(x)
        ax.set_xticklabels(body_parts, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

    def create_total_segmental_trends_chart(self, segmental_history_df: pd.DataFrame) -> io.BytesIO:
        """Create a chart showing total lean vs fat mass trends across all body parts."""
        if segmental_history_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No segmental data available', transform=ax.transAxes, ha='center', va='center')
            return self._finalize_chart(ax, 'Total Segmental Trends')

        fig, ax = plt.subplots(figsize=(12, 8))

        # Calculate total lean and fat mass across all body parts
        lean_cols = ['right_arm_lean', 'left_arm_lean', 'trunk_lean', 'right_leg_lean', 'left_leg_lean']
        fat_cols = ['right_arm_fat', 'left_arm_fat', 'trunk_fat', 'right_leg_fat', 'left_leg_fat']

        # Create totals
        df = segmental_history_df.copy()
        df['total_lean'] = df[lean_cols].sum(axis=1, skipna=True)
        df['total_fat'] = df[fat_cols].sum(axis=1, skipna=True)

        # Filter out rows where both totals are 0 or NaN
        df = df[(df['total_lean'] > 0) | (df['total_fat'] > 0)].copy()

        if not df.empty:
            # Plot total trends
            ax.plot(
                df['scan_date'],
                df['total_lean'],
                color=self.colors['success'],
                linewidth=3,
                marker='o',
                label='Total Lean Mass',
                markersize=6,
            )

            ax.plot(
                df['scan_date'],
                df['total_fat'],
                color=self.colors['secondary'],
                linewidth=3,
                marker='s',
                label='Total Fat Mass',
                markersize=6,
            )

            # Add trend lines
            if len(df) > 2:
                # Simple linear trend
                x_numeric = (df['scan_date'] - df['scan_date'].min()).dt.days

                lean_trend = np.polyfit(x_numeric, df['total_lean'], 1)
                fat_trend = np.polyfit(x_numeric, df['total_fat'], 1)

                lean_line = np.poly1d(lean_trend)
                fat_line = np.poly1d(fat_trend)

                ax.plot(
                    df['scan_date'],
                    lean_line(x_numeric),
                    color=self.colors['success'],
                    linestyle='--',
                    alpha=0.6,
                    linewidth=2,
                    label='Lean Mass Trend',
                )

                ax.plot(
                    df['scan_date'],
                    fat_line(x_numeric),
                    color=self.colors['secondary'],
                    linestyle='--',
                    alpha=0.6,
                    linewidth=2,
                    label='Fat Mass Trend',
                )

        ax.set_title('Total Body Segmental Mass Trends', fontweight='bold', fontsize=14, pad=15)
        ax.set_ylabel('Mass (kg)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10)

        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def create_control_recommendations_chart(self, df: pd.DataFrame) -> io.BytesIO:
        """Create chart showing InBody's muscle and fat control recommendations over time."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Filter data with control recommendations
        control_data = df[['scan_date', 'muscle_control', 'fat_control']].dropna(
            subset=['muscle_control', 'fat_control'], how='all'
        )

        if control_data.empty:
            for ax in [ax1, ax2]:
                ax.text(
                    0.5,
                    0.5,
                    'No control recommendation data available',
                    transform=ax.transAxes,
                    ha='center',
                    va='center',
                    fontsize=12,
                )
        else:
            # Muscle Control Recommendations
            muscle_data = control_data[control_data['muscle_control'].notna()]
            if not muscle_data.empty:
                ax1.plot(
                    muscle_data['scan_date'],
                    muscle_data['muscle_control'],
                    color=self.colors['success'],
                    linewidth=3,
                    marker='o',
                    markersize=6,
                )

                # Add zero line for reference
                ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5, label='Ideal Target')

                # Color fill based on positive/negative
                for i in range(len(muscle_data) - 1):
                    y_val = muscle_data['muscle_control'].iloc[i]
                    color = self.colors['success'] if y_val > 0 else self.colors['secondary']
                    ax1.fill_between(muscle_data['scan_date'].iloc[i : i + 2], y_val, 0, alpha=0.3, color=color)

            ax1.set_title('Muscle Control Recommendations', fontweight='bold', pad=20)
            ax1.set_ylabel('Recommended Muscle Change (kg)')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

            # Fat Control Recommendations
            fat_data = control_data[control_data['fat_control'].notna()]
            if not fat_data.empty:
                ax2.plot(
                    fat_data['scan_date'],
                    fat_data['fat_control'],
                    color=self.colors['secondary'],
                    linewidth=3,
                    marker='s',
                    markersize=6,
                )

                # Add zero line for reference
                ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5, label='Ideal Target')

                # Color fill based on positive/negative
                for i in range(len(fat_data) - 1):
                    y_val = fat_data['fat_control'].iloc[i]
                    color = self.colors['secondary'] if y_val < 0 else self.colors['accent']
                    ax2.fill_between(fat_data['scan_date'].iloc[i : i + 2], y_val, 0, alpha=0.3, color=color)

            ax2.set_title('Fat Control Recommendations', fontweight='bold', pad=20)
            ax2.set_ylabel('Recommended Fat Change (kg)')
            ax2.set_xlabel('Date')
            ax2.grid(True, alpha=0.3)
            ax2.legend()

            # Format dates for both subplots
            for ax in [ax1, ax2]:
                ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.subplots_adjust(hspace=0.3)

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def create_body_metrics_chart(self, df: pd.DataFrame) -> io.BytesIO:
        """Create chart showing WHR (waist-hip ratio) and total body water trends."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # WHR (Waist-Hip Ratio)
        whr_data = df[['scan_date', 'whr']].dropna()
        if not whr_data.empty:
            ax1.plot(
                whr_data['scan_date'],
                whr_data['whr'],
                color=self.colors['accent'],
                linewidth=3,
                marker='o',
                markersize=6,
            )

            # Add healthy WHR ranges (general guidelines)
            ax1.axhspan(0.8, 0.9, alpha=0.2, color=self.colors['success'], label='Healthy Range (approx)')
            ax1.axhspan(0.9, 1.0, alpha=0.2, color=self.colors['accent'], label='Caution Range')

            ax1.set_title('Waist-Hip Ratio (WHR)', fontweight='bold', pad=20)
            ax1.set_ylabel('WHR')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
        else:
            ax1.text(0.5, 0.5, 'No WHR data available', transform=ax1.transAxes, ha='center', va='center', fontsize=12)
            ax1.set_title('Waist-Hip Ratio (WHR)', fontweight='bold', pad=20)

        # Total Body Water
        tbw_data = df[['scan_date', 'total_body_water']].dropna()
        if not tbw_data.empty:
            ax2.plot(
                tbw_data['scan_date'],
                tbw_data['total_body_water'],
                color=self.colors['info'],
                linewidth=3,
                marker='s',
                markersize=6,
            )

            ax2.set_title('Total Body Water', fontweight='bold', pad=20)
            ax2.set_ylabel('Total Body Water (L)')
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(
                0.5, 0.5, 'No body water data available', transform=ax2.transAxes, ha='center', va='center', fontsize=12
            )
            ax2.set_title('Total Body Water', fontweight='bold', pad=20)

        # Format dates for both subplots
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)
            ax.set_xlabel('Date')

        plt.tight_layout()

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def create_advanced_composition_chart(self, df: pd.DataFrame) -> io.BytesIO:
        """Create chart showing PBF and Fat-Free Mass trends."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # PBF (Percent Body Fat) - might be different from body_fat_percentage
        pbf_data = df[['scan_date', 'pbf', 'body_fat_percentage']].dropna(subset=['pbf'])
        if not pbf_data.empty:
            ax1.plot(
                pbf_data['scan_date'],
                pbf_data['pbf'],
                color=self.colors['secondary'],
                linewidth=3,
                marker='o',
                markersize=6,
                label='PBF',
            )

            # Also plot body_fat_percentage if different from PBF
            if 'body_fat_percentage' in pbf_data.columns and pbf_data['body_fat_percentage'].notna().any():
                # Check if PBF and body_fat_percentage are significantly different
                diff_exists = (abs(pbf_data['pbf'] - pbf_data['body_fat_percentage']) > 0.5).any()
                if diff_exists:
                    ax1.plot(
                        pbf_data['scan_date'],
                        pbf_data['body_fat_percentage'],
                        color=self.colors['accent'],
                        linewidth=2,
                        marker='^',
                        markersize=5,
                        label='Body Fat %',
                        linestyle='--',
                    )

            ax1.set_title('Percent Body Fat (PBF)', fontweight='bold', pad=20)
            ax1.set_ylabel('Body Fat (%)')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
        else:
            ax1.text(0.5, 0.5, 'No PBF data available', transform=ax1.transAxes, ha='center', va='center', fontsize=12)
            ax1.set_title('Percent Body Fat (PBF)', fontweight='bold', pad=20)

        # Fat-Free Mass
        ffm_data = df[['scan_date', 'fat_free_mass']].dropna()
        if not ffm_data.empty:
            ax2.plot(
                ffm_data['scan_date'],
                ffm_data['fat_free_mass'],
                color=self.colors['success'],
                linewidth=3,
                marker='s',
                markersize=6,
            )

            ax2.set_title('Fat-Free Mass', fontweight='bold', pad=20)
            ax2.set_ylabel('Fat-Free Mass (kg)')
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(
                0.5,
                0.5,
                'No fat-free mass data available',
                transform=ax2.transAxes,
                ha='center',
                va='center',
                fontsize=12,
            )
            ax2.set_title('Fat-Free Mass', fontweight='bold', pad=20)

        # Format dates for both subplots
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)
            ax.set_xlabel('Date')

        plt.tight_layout()

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def create_progress_comparison_chart(self, comparison_df: pd.DataFrame) -> io.BytesIO:
        """Create before/after comparison chart."""
        if comparison_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(
                0.5, 0.5, 'No comparison data available', transform=ax.transAxes, ha='center', va='center', fontsize=14
            )
            ax.set_title('Progress Comparison')
            plt.tight_layout()
        else:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))

            # Before/After comparison
            metrics = comparison_df['metric']
            first_values = comparison_df['first_scan']
            last_values = comparison_df['last_scan']

            x_pos = range(len(metrics))
            width = 0.35

            bars1 = ax1.bar(
                [x - width / 2 for x in x_pos],
                first_values,
                width,
                label='First Scan',
                color=self.colors['light'],
                alpha=0.8,
            )
            bars2 = ax1.bar(
                [x + width / 2 for x in x_pos],
                last_values,
                width,
                label='Latest Scan',
                color=self.colors['primary'],
                alpha=0.8,
            )

            ax1.set_xlabel('Metrics')
            ax1.set_ylabel('Values')
            ax1.set_title('First vs Latest Scan Comparison', fontweight='bold')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(metrics, rotation=45)
            ax1.legend()
            ax1.grid(True, alpha=0.3, axis='y')

            # Add value labels
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax1.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f'{height:.1f}',
                        ha='center',
                        va='bottom',
                        fontsize=9,
                    )

            # Change visualization
            changes = comparison_df['change']
            colors = [self.colors['success'] if x >= 0 else self.colors['secondary'] for x in changes]

            bars3 = ax2.bar(x_pos, changes, color=colors, alpha=0.8)
            ax2.set_xlabel('Metrics')
            ax2.set_ylabel('Change')
            ax2.set_title('Change from First to Latest Scan', fontweight='bold')
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels(metrics, rotation=45)
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax2.grid(True, alpha=0.3, axis='y')

            # Add value labels for changes
            for bar in bars3:
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f'{height:+.1f}',
                    ha='center',
                    va='bottom' if height >= 0 else 'top',
                    fontsize=9,
                )

        plt.tight_layout()

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def create_summary_dashboard(self, df: pd.DataFrame, stats: dict) -> io.BytesIO:
        """Create a summary dashboard with key metrics."""
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

        # Title
        fig.suptitle('InBody Progress Dashboard', fontsize=20, fontweight='bold', y=0.95)

        # Key metrics boxes
        if 'weight_change' in stats:
            ax1 = fig.add_subplot(gs[0, 0])
            self._create_metric_box(
                ax1, 'Weight Change', f'{stats["weight_change"]["total_kg"]:+.1f} kg', self.colors['primary']
            )

        if 'body_fat_change' in stats:
            ax2 = fig.add_subplot(gs[0, 1])
            self._create_metric_box(
                ax2, 'Body Fat Change', f'{stats["body_fat_change"]["total_percent"]:+.1f}%', self.colors['secondary']
            )

        if 'muscle_change' in stats:
            ax3 = fig.add_subplot(gs[0, 2])
            self._create_metric_box(
                ax3, 'Muscle Change', f'{stats["muscle_change"]["total_kg"]:+.1f} kg', self.colors['success']
            )

        ax4 = fig.add_subplot(gs[0, 3])
        self._create_metric_box(ax4, 'Total Scans', f'{stats["total_scans"]}', self.colors['info'])

        # BMI progression chart (instead of duplicating weight)
        ax5 = fig.add_subplot(gs[1, :2])
        bmi_data = df[df['bmi'].notna()]
        if not bmi_data.empty:
            ax5.plot(
                bmi_data['scan_date'],
                bmi_data['bmi'],
                color=self.colors['info'],
                linewidth=2,
                marker='o',
                markersize=4,
            )
            # Add healthy BMI range shading
            ax5.axhspan(18.5, 25, alpha=0.2, color=self.colors['success'], label='Healthy Range')
            ax5.set_title('BMI Progression', fontweight='bold')
            ax5.set_ylabel('BMI')
            ax5.grid(True, alpha=0.3)
            ax5.legend()
        else:
            ax5.text(0.5, 0.5, 'No BMI data available', transform=ax5.transAxes, ha='center', va='center')
            ax5.set_title('BMI Progression', fontweight='bold')

        # Body Fat Percentage trend (clearer focus)
        ax6 = fig.add_subplot(gs[1, 2:])
        bf_data = df[df['body_fat_percentage'].notna()]
        if not bf_data.empty:
            ax6.plot(
                bf_data['scan_date'],
                bf_data['body_fat_percentage'],
                color=self.colors['secondary'],
                linewidth=2,
                marker='s',
                markersize=4,
            )
            # Add healthy body fat range (example - varies by gender/age)
            ax6.axhspan(10, 20, alpha=0.2, color=self.colors['success'], label='Healthy Range (example)')
            ax6.set_title('Body Fat Percentage Trend', fontweight='bold')
            ax6.set_ylabel('Body Fat (%)')
            ax6.grid(True, alpha=0.3)
            ax6.legend()
        else:
            ax6.text(0.5, 0.5, 'No body fat data available', transform=ax6.transAxes, ha='center', va='center')
            ax6.set_title('Body Fat Percentage Trend', fontweight='bold')

        # Stats text
        ax7 = fig.add_subplot(gs[2, :])
        ax7.axis('off')

        # Create stats text
        stats_text = self._format_stats_text(stats)
        ax7.text(
            0.5,
            0.5,
            stats_text,
            transform=ax7.transAxes,
            ha='center',
            va='center',
            fontsize=12,
            bbox=dict(boxstyle='round,pad=0.5', facecolor=self.colors['light'], alpha=0.3),
        )

        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=self.dpi)
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    def _create_metric_box(self, ax, title: str, value: str, color: str):
        """Create a metric box for the dashboard."""
        ax.text(0.5, 0.7, title, transform=ax.transAxes, ha='center', fontsize=10, fontweight='bold')
        ax.text(0.5, 0.3, value, transform=ax.transAxes, ha='center', fontsize=16, fontweight='bold', color=color)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Add border
        for spine in ['top', 'bottom', 'left', 'right']:
            ax.spines[spine].set_visible(True)
            ax.spines[spine].set_color(color)
            ax.spines[spine].set_linewidth(2)

    def _format_stats_text(self, stats: dict) -> str:
        """Format statistics into readable text."""
        lines = []

        if 'date_range' in stats:
            lines.append(f'Tracking Period: {stats["date_range"]["days"]} days')

        if 'weight_change' in stats:
            wc = stats['weight_change']
            lines.append(f'Weight: {wc["start_weight"]}kg → {wc["end_weight"]}kg ({wc["total_kg"]:+.1f}kg)')

        if 'bmi_change' in stats:
            bc = stats['bmi_change']
            lines.append(f'BMI: {bc["start_bmi"]:.1f} → {bc["end_bmi"]:.1f} ({bc["total"]:+.1f})')

        return '\n'.join(lines)
