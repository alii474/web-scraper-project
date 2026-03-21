"""
Data Visualization Module

Creates comprehensive visualizations for scraped data using matplotlib.
Supports multiple chart types and automatic data analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..utils.logger import get_logger
from ..utils.config import CONFIG


class DataVisualizer:
    """
    Advanced data visualization for scraped data.
    
    Features:
    - Multiple chart types
    - Automatic data analysis
    - Professional styling
    - Export capabilities
    - Statistical summaries
    """
    
    def __init__(self):
        self.logger = get_logger('visualizer')
        
        # Setup matplotlib style
        self._setup_style()
        
        # Create output directory
        self.output_dir = Path(__file__).parent.parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def _setup_style(self):
        """Setup matplotlib and seaborn styling."""
        try:
            # Set seaborn style
            sns.set_style("whitegrid")
            
            # Set color palette
            self.colors = sns.color_palette("husl", 10)
            
            # Set font sizes
            plt.rcParams.update({
                'font.size': 12,
                'axes.titlesize': 14,
                'axes.labelsize': 12,
                'xtick.labelsize': 10,
                'ytick.labelsize': 10,
                'legend.fontsize': 10,
                'figure.titlesize': 16
            })
            
            # Set figure quality
            plt.rcParams.update({
                'figure.dpi': CONFIG.CHART_DPI,
                'savefig.dpi': CONFIG.CHART_DPI,
                'savefig.bbox': 'tight',
                'savefig.format': 'png'
            })
        
        except Exception as e:
            self.logger.warning(f"Failed to setup matplotlib style: {e}")
    
    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze scraped data and generate insights.
        
        Args:
            df: DataFrame containing scraped data
        
        Returns:
            Analysis results
        """
        analysis = {
            'total_records': len(df),
            'columns': list(df.columns),
            'data_types': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
            'categorical_columns': list(df.select_dtypes(include=['object']).columns)
        }
        
        # Numeric statistics
        if analysis['numeric_columns']:
            analysis['numeric_stats'] = df[analysis['numeric_columns']].describe().to_dict()
        
        # Categorical statistics
        if analysis['categorical_columns']:
            analysis['categorical_stats'] = {}
            for col in analysis['categorical_columns']:
                analysis['categorical_stats'][col] = {
                    'unique_count': df[col].nunique(),
                    'top_values': df[col].value_counts().head(10).to_dict()
                }
        
        return analysis
    
    def create_price_distribution(self, df: pd.DataFrame, price_col: str = 'price') -> plt.Figure:
        """
        Create price distribution histogram.
        
        Args:
            df: DataFrame containing data
            price_col: Column name for price data
        
        Returns:
            Matplotlib figure
        """
        if price_col not in df.columns:
            raise ValueError(f"Price column '{price_col}' not found")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Histogram
        ax1.hist(df[price_col].dropna(), bins=30, alpha=0.7, color=self.colors[0], edgecolor='black')
        ax1.set_title('Price Distribution', fontweight='bold')
        ax1.set_xlabel('Price')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        ax2.boxplot(df[price_col].dropna(), patch_artist=True, 
                   boxprops=dict(facecolor=self.colors[1], alpha=0.7))
        ax2.set_title('Price Box Plot', fontweight='bold')
        ax2.set_ylabel('Price')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_rating_analysis(self, df: pd.DataFrame, rating_col: str = 'rating', 
                            price_col: str = 'price') -> plt.Figure:
        """
        Create rating analysis charts.
        
        Args:
            df: DataFrame containing data
            rating_col: Column name for rating data
            price_col: Column name for price data
        
        Returns:
            Matplotlib figure
        """
        if rating_col not in df.columns:
            raise ValueError(f"Rating column '{rating_col}' not found")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Rating distribution
        rating_counts = df[rating_col].value_counts().sort_index()
        bars = ax1.bar(rating_counts.index, rating_counts.values, 
                      color=self.colors[:len(rating_counts)], alpha=0.7, edgecolor='black')
        ax1.set_title('Rating Distribution', fontweight='bold')
        ax1.set_xlabel('Rating')
        ax1.set_ylabel('Count')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')
        
        # Rating pie chart
        ax2.pie(rating_counts.values, labels=rating_counts.index, autopct='%1.1f%%',
               colors=self.colors[:len(rating_counts)], startangle=90)
        ax2.set_title('Rating Share', fontweight='bold')
        
        # Price by rating (if price column available)
        if price_col in df.columns:
            rating_price = df.groupby(rating_col)[price_col].mean()
            bars = ax3.bar(rating_price.index, rating_price.values,
                          color=self.colors[:len(rating_price)], alpha=0.7, edgecolor='black')
            ax3.set_title('Average Price by Rating', fontweight='bold')
            ax3.set_xlabel('Rating')
            ax3.set_ylabel('Average Price')
            ax3.grid(True, alpha=0.3)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                       f'£{height:.2f}', ha='center', va='bottom')
        else:
            ax3.text(0.5, 0.5, 'Price data not available', 
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Price Analysis Unavailable', fontweight='bold')
        
        # Rating vs price scatter (if both available)
        if price_col in df.columns:
            # Convert rating to numeric for scatter plot
            rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
            df_numeric = df.copy()
            df_numeric['rating_numeric'] = df_numeric[rating_col].map(rating_map)
            
            scatter_data = df_numeric.dropna(subset=['rating_numeric', price_col])
            if not scatter_data.empty:
                ax4.scatter(scatter_data['rating_numeric'], scatter_data[price_col],
                           alpha=0.6, color=self.colors[0], s=50)
                ax4.set_title('Rating vs Price Scatter', fontweight='bold')
                ax4.set_xlabel('Rating')
                ax4.set_ylabel('Price')
                ax4.grid(True, alpha=0.3)
                
                # Add trend line
                z = np.polyfit(scatter_data['rating_numeric'], scatter_data[price_col], 1)
                p = np.poly1d(z)
                ax4.plot(scatter_data['rating_numeric'], p(scatter_data['rating_numeric']),
                        "r--", alpha=0.8, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
                ax4.legend()
            else:
                ax4.text(0.5, 0.5, 'Insufficient data for scatter plot', 
                        ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title('Scatter Plot Unavailable', fontweight='bold')
        else:
            ax4.text(0.5, 0.5, 'Price data not available', 
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Scatter Plot Unavailable', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def create_temporal_analysis(self, df: pd.DataFrame, date_col: str = 'parsed_at') -> plt.Figure:
        """
        Create temporal analysis charts.
        
        Args:
            df: DataFrame containing data
            date_col: Column name for date data
        
        Returns:
            Matplotlib figure
        """
        if date_col not in df.columns:
            raise ValueError(f"Date column '{date_col}' not found")
        
        # Convert date column to datetime
        df[date_col] = pd.to_datetime(df[date_col])
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Items over time (daily)
        daily_counts = df.groupby(df[date_col].dt.date).size()
        ax1.plot(daily_counts.index, daily_counts.values, marker='o', 
                color=self.colors[0], linewidth=2, markersize=6)
        ax1.set_title('Items Scraped Over Time (Daily)', fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Number of Items')
        ax1.grid(True, alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Items over time (hourly)
        hourly_counts = df.groupby(df[date_col].dt.hour).size()
        ax2.bar(hourly_counts.index, hourly_counts.values, 
               color=self.colors[1], alpha=0.7, edgecolor='black')
        ax2.set_title('Items Scraped by Hour', fontweight='bold')
        ax2.set_xlabel('Hour of Day')
        ax2.set_ylabel('Number of Items')
        ax2.grid(True, alpha=0.3)
        
        # Day of week analysis
        df['day_of_week'] = df[date_col].dt.day_name()
        dow_counts = df['day_of_week'].value_counts()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_counts = dow_counts.reindex(day_order, fill_value=0)
        
        bars = ax3.bar(dow_counts.index, dow_counts.values,
                       color=self.colors[2], alpha=0.7, edgecolor='black')
        ax3.set_title('Items Scraped by Day of Week', fontweight='bold')
        ax3.set_xlabel('Day of Week')
        ax3.set_ylabel('Number of Items')
        ax3.grid(True, alpha=0.3)
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')
        
        # Scraping performance (items per hour)
        df['hour'] = df[date_col].dt.hour
        hourly_performance = df.groupby('hour').size()
        
        if len(hourly_performance) > 1:
            ax4.plot(hourly_performance.index, hourly_performance.values, 
                    marker='s', color=self.colors[3], linewidth=2, markersize=6)
            ax4.set_title('Scraping Performance by Hour', fontweight='bold')
            ax4.set_xlabel('Hour of Day')
            ax4.set_ylabel('Items Scraped')
            ax4.grid(True, alpha=0.3)
            
            # Highlight peak hours
            peak_hour = hourly_performance.idxmax()
            peak_value = hourly_performance.max()
            ax4.annotate(f'Peak: {peak_value} items\nat {peak_hour}:00',
                        xy=(peak_hour, peak_value), xytext=(peak_hour+1, peak_value*0.8),
                        arrowprops=dict(arrowstyle='->', color='red'),
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        else:
            ax4.text(0.5, 0.5, 'Insufficient data for performance analysis', 
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Performance Analysis Unavailable', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def create_data_quality_analysis(self, df: pd.DataFrame) -> plt.Figure:
        """
        Create data quality analysis charts.
        
        Args:
            df: DataFrame containing data
        
        Returns:
            Matplotlib figure
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Missing values analysis
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
        
        if not missing_data.empty:
            bars = ax1.barh(range(len(missing_data)), missing_data.values,
                           color=self.colors[0], alpha=0.7, edgecolor='black')
            ax1.set_yticks(range(len(missing_data)))
            ax1.set_yticklabels(missing_data.index)
            ax1.set_title('Missing Values by Column', fontweight='bold')
            ax1.set_xlabel('Number of Missing Values')
            ax1.grid(True, alpha=0.3)
            
            # Add value labels
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax1.text(width, bar.get_y() + bar.get_height()/2.,
                        f'{int(width)}', ha='left', va='center')
        else:
            ax1.text(0.5, 0.5, 'No missing values found!', 
                    ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Missing Values Analysis', fontweight='bold')
        
        # Data types distribution
        dtype_counts = df.dtypes.value_counts()
        ax2.pie(dtype_counts.values, labels=dtype_counts.index, autopct='%1.1f%%',
               colors=self.colors[:len(dtype_counts)], startangle=90)
        ax2.set_title('Data Types Distribution', fontweight='bold')
        
        # Column completeness
        completeness = (1 - df.isnull().sum() / len(df)) * 100
        completeness = completeness.sort_values(ascending=False)
        
        bars = ax3.barh(range(len(completeness)), completeness.values,
                       color=self.colors[2], alpha=0.7, edgecolor='black')
        ax3.set_yticks(range(len(completeness)))
        ax3.set_yticklabels(completeness.index)
        ax3.set_title('Column Completeness (%)', fontweight='bold')
        ax3.set_xlabel('Completeness (%)')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax3.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{width:.1f}%', ha='left', va='center')
        
        # Data quality score
        quality_score = completeness.mean()
        
        # Create gauge chart for quality score
        ax4.clear()
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta)
        
        # Background arc
        ax4.fill_between(theta, 0, r, color='lightgray', alpha=0.3)
        
        # Quality score arc
        quality_theta = np.linspace(0, np.pi * (quality_score / 100), 100)
        quality_color = 'green' if quality_score > 80 else 'yellow' if quality_score > 60 else 'red'
        ax4.fill_between(quality_theta, 0, r, color=quality_color, alpha=0.7)
        
        ax4.set_xlim(-1.2, 1.2)
        ax4.set_ylim(-0.2, 1.2)
        ax4.set_aspect('equal')
        ax4.axis('off')
        
        ax4.text(0, 0.5, f'{quality_score:.1f}%', ha='center', va='center',
                fontsize=24, fontweight='bold')
        ax4.text(0, 0.3, 'Data Quality Score', ha='center', va='center',
                fontsize=12)
        
        # Add quality labels
        ax4.text(-0.8, 0.1, 'Poor', ha='center', fontsize=10)
        ax4.text(0, -0.1, 'Good', ha='center', fontsize=10)
        ax4.text(0.8, 0.1, 'Excellent', ha='center', fontsize=10)
        
        ax4.set_title('Overall Data Quality', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def create_comprehensive_analysis(self, df: pd.DataFrame, 
                                   filename_prefix: str = "scraped_data") -> str:
        """
        Create comprehensive data analysis with multiple visualizations.
        
        Args:
            df: DataFrame containing scraped data
            filename_prefix: Prefix for output filename
        
        Returns:
            Path to saved visualization file
        """
        if df.empty:
            self.logger.warning("Empty DataFrame provided for visualization")
            return ""
        
        try:
            # Analyze data
            analysis = self.analyze_data(df)
            self.logger.info(f"Data analysis: {analysis['total_records']} records, "
                           f"{len(analysis['numeric_columns'])} numeric columns, "
                           f"{len(analysis['categorical_columns'])} categorical columns")
            
            # Create figure with subplots
            fig = plt.figure(figsize=(20, 24))
            
            # Define subplot layout
            gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
            
            # 1. Summary statistics
            ax_summary = fig.add_subplot(gs[0, :])
            self._create_summary_table(ax_summary, analysis, df)
            
            # 2. Price analysis (if price column exists)
            if 'price' in df.columns:
                ax_price_hist = fig.add_subplot(gs[1, 0])
                ax_price_box = fig.add_subplot(gs[1, 1])
                self._create_price_charts(df, ax_price_hist, ax_price_box)
            else:
                ax_missing = fig.add_subplot(gs[1, :])
                ax_missing.text(0.5, 0.5, 'Price data not available for analysis',
                               ha='center', va='center', transform=ax_missing.transAxes,
                               fontsize=14)
                ax_missing.set_title('Price Analysis', fontweight='bold')
            
            # 3. Rating analysis (if rating column exists)
            if 'rating' in df.columns:
                ax_rating_dist = fig.add_subplot(gs[1, 2])
                ax_rating_price = fig.add_subplot(gs[2, 0])
                self._create_rating_charts(df, ax_rating_dist, ax_rating_price)
            else:
                ax_missing = fig.add_subplot(gs[1, 2])
                ax_missing.text(0.5, 0.5, 'Rating data not available for analysis',
                               ha='center', va='center', transform=ax_missing.transAxes,
                               fontsize=14)
                ax_missing.set_title('Rating Analysis', fontweight='bold')
            
            # 4. Data quality analysis
            ax_quality = fig.add_subplot(gs[2, 1:])
            self._create_quality_chart(df, ax_quality)
            
            # 5. Temporal analysis (if date column exists)
            if 'parsed_at' in df.columns:
                ax_temporal = fig.add_subplot(gs[3, :])
                self._create_temporal_chart(df, ax_temporal)
            else:
                ax_missing = fig.add_subplot(gs[3, :])
                ax_missing.text(0.5, 0.5, 'Temporal data not available for analysis',
                               ha='center', va='center', transform=ax_missing.transAxes,
                               fontsize=14)
                ax_missing.set_title('Temporal Analysis', fontweight='bold')
            
            # Save the figure
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_analysis_{timestamp}.png"
            output_path = self.output_dir / filename
            
            plt.savefig(output_path, dpi=CONFIG.CHART_DPI, bbox_inches='tight')
            self.logger.info(f"Comprehensive analysis saved to: {output_path}")
            
            # Show the plot
            plt.show()
            
            return str(output_path)
        
        except Exception as e:
            self.logger.error(f"Failed to create comprehensive analysis: {e}")
            raise
    
    def _create_summary_table(self, ax, analysis: Dict[str, Any], df: pd.DataFrame):
        """Create summary statistics table."""
        ax.axis('off')
        
        # Create summary data
        summary_data = [
            ['Total Records', f"{analysis['total_records']:,}"],
            ['Total Columns', str(len(analysis['columns']))],
            ['Numeric Columns', str(len(analysis['numeric_columns']))],
            ['Categorical Columns', str(len(analysis['categorical_columns']))],
            ['Missing Values', str(sum(analysis['missing_values'].values()))],
            ['Data Quality Score', f"{(1 - sum(analysis['missing_values'].values()) / (len(df) * len(analysis['columns'])) * 100):.1f}%"]
        ]
        
        # Add price statistics if available
        if 'price' in analysis['numeric_stats']:
            price_stats = analysis['numeric_stats']['price']
            summary_data.extend([
                ['Price Range', f"£{price_stats['min']:.2f} - £{price_stats['max']:.2f}"],
                ['Average Price', f"£{price_stats['mean']:.2f}"]
            ])
        
        # Add rating statistics if available
        if 'rating' in analysis['categorical_stats']:
            rating_stats = analysis['categorical_stats']['rating']
            top_rating = max(rating_stats['top_values'].items(), key=lambda x: x[1])
            summary_data.extend([
                ['Rating Categories', str(rating_stats['unique_count'])],
                ['Top Rating', f"{top_rating[0]} ({top_rating[1]} items)"]
            ])
        
        # Create table
        table = ax.table(cellText=summary_data, 
                       colLabels=['Metric', 'Value'],
                       cellLoc='center',
                       loc='center',
                       colWidths=[0.6, 0.4])
        
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2)
        
        # Style the table
        for i in range(len(summary_data) + 1):
            for j in range(2):
                cell = table[i, j]
                if i == 0:  # Header row
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        
        ax.set_title('📊 Data Summary', fontweight='bold', fontsize=16, pad=20)
    
    def _create_price_charts(self, df: pd.DataFrame, ax_hist, ax_box):
        """Create price distribution charts."""
        price_data = df['price'].dropna()
        
        # Histogram
        ax_hist.hist(price_data, bins=20, alpha=0.7, color=self.colors[0], edgecolor='black')
        ax_hist.set_title('Price Distribution', fontweight='bold')
        ax_hist.set_xlabel('Price (£)')
        ax_hist.set_ylabel('Frequency')
        ax_hist.grid(True, alpha=0.3)
        
        # Box plot
        ax_box.boxplot(price_data, patch_artist=True, 
                      boxprops=dict(facecolor=self.colors[1], alpha=0.7))
        ax_box.set_title('Price Box Plot', fontweight='bold')
        ax_box.set_ylabel('Price (£)')
        ax_box.grid(True, alpha=0.3)
    
    def _create_rating_charts(self, df: pd.DataFrame, ax_dist, ax_price):
        """Create rating analysis charts."""
        rating_counts = df['rating'].value_counts().sort_index()
        
        # Rating distribution
        bars = ax_dist.bar(rating_counts.index, rating_counts.values,
                          color=self.colors[:len(rating_counts)], alpha=0.7, edgecolor='black')
        ax_dist.set_title('Rating Distribution', fontweight='bold')
        ax_dist.set_xlabel('Rating')
        ax_dist.set_ylabel('Count')
        ax_dist.grid(True, alpha=0.3)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax_dist.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
        
        # Average price by rating
        if 'price' in df.columns:
            rating_price = df.groupby('rating')['price'].mean()
            bars = ax_price.bar(rating_price.index, rating_price.values,
                              color=self.colors[:len(rating_price)], alpha=0.7, edgecolor='black')
            ax_price.set_title('Avg Price by Rating', fontweight='bold')
            ax_price.set_xlabel('Rating')
            ax_price.set_ylabel('Average Price (£)')
            ax_price.grid(True, alpha=0.3)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax_price.text(bar.get_x() + bar.get_width()/2., height,
                            f'£{height:.2f}', ha='center', va='bottom')
        else:
            ax_price.text(0.5, 0.5, 'Price data not available',
                         ha='center', va='center', transform=ax_price.transAxes)
            ax_price.set_title('Price Analysis Unavailable', fontweight='bold')
    
    def _create_quality_chart(self, df: pd.DataFrame, ax):
        """Create data quality chart."""
        missing_data = df.isnull().sum()
        completeness = (1 - missing_data / len(df)) * 100
        
        bars = ax.barh(range(len(completeness)), completeness.values,
                      color=self.colors[2], alpha=0.7, edgecolor='black')
        ax.set_yticks(range(len(completeness)))
        ax.set_yticklabels(completeness.index)
        ax.set_title('Data Quality by Column', fontweight='bold')
        ax.set_xlabel('Completeness (%)')
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{width:.1f}%', ha='left', va='center')
    
    def _create_temporal_chart(self, df: pd.DataFrame, ax):
        """Create temporal analysis chart."""
        df['parsed_at'] = pd.to_datetime(df['parsed_at'])
        daily_counts = df.groupby(df['parsed_at'].dt.date).size()
        
        ax.plot(daily_counts.index, daily_counts.values, marker='o',
               color=self.colors[3], linewidth=2, markersize=6)
        ax.set_title('Items Scraped Over Time', fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Items')
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
