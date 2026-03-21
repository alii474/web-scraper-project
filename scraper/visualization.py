# scraper/visualization.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
import logging

class DataVisualizer:
    """
    Create visualizations for scraped book data.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Set style
        try:
            plt.style.use('seaborn-v0_8')
        except:
            plt.style.use('default')

        # Create data directory if it doesn't exist
        Path('data').mkdir(exist_ok=True)

    def create_price_distribution(self, df, ax):
        """Create price distribution histogram."""
        ax.hist(df['price'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax.set_title('Price Distribution')
        ax.set_xlabel('Price (£)')
        ax.set_ylabel('Number of Books')
        ax.grid(True, alpha=0.3)

    def create_rating_distribution(self, df, ax):
        """Create rating distribution bar chart."""
        rating_counts = df['rating'].value_counts()
        rating_order = ['One', 'Two', 'Three', 'Four', 'Five']
        rating_counts = rating_counts.reindex(rating_order).fillna(0)

        bars = ax.bar(rating_counts.index, rating_counts.values,
                     color='lightgreen', alpha=0.7, edgecolor='black')
        ax.set_title('Rating Distribution')
        ax.set_xlabel('Rating')
        ax.set_ylabel('Number of Books')

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')

    def create_price_by_rating(self, df, ax):
        """Create average price by rating chart."""
        rating_order = ['One', 'Two', 'Three', 'Four', 'Five']
        rating_price = df.groupby('rating')['price'].mean().reindex(rating_order)

        bars = ax.bar(rating_order, rating_price.values,
                     color='orange', alpha=0.7, edgecolor='black')
        ax.set_title('Average Price by Rating')
        ax.set_xlabel('Rating')
        ax.set_ylabel('Average Price (£)')
        ax.grid(True, alpha=0.3)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'£{height:.2f}', ha='center', va='bottom')

    def create_availability_pie(self, df, ax):
        """Create availability status pie chart."""
        availability_counts = df['availability'].value_counts()

        colors = ['lightcoral', 'lightblue', 'lightgreen', 'gold']
        wedges, texts, autotexts = ax.pie(availability_counts.values,
                                        labels=availability_counts.index,
                                        autopct='%1.1f%%',
                                        colors=colors[:len(availability_counts)],
                                        startangle=90)

        ax.set_title('Book Availability Status')

        # Improve text readability
        for text in texts:
            text.set_fontsize(8)
        for autotext in autotexts:
            autotext.set_fontsize(8)

    def create_comprehensive_analysis(self, df, filename_prefix="books_analysis"):
        """
        Create comprehensive data analysis visualizations.

        Args:
            df: DataFrame with book data
            filename_prefix: Prefix for output filename
        """
        if df.empty:
            self.logger.warning("No data to visualize")
            return

        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('📊 Book Data Analysis Dashboard', fontsize=16, fontweight='bold', y=0.95)

        # Create individual plots
        self.create_price_distribution(df, ax1)
        self.create_rating_distribution(df, ax2)
        self.create_price_by_rating(df, ax3)
        self.create_availability_pie(df, ax4)

        plt.tight_layout()

        # Save the plot
        output_path = f"data/{filename_prefix}_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        self.logger.info(f"Analysis visualization saved to: {output_path}")

        # Show the plot
        plt.show()

        return output_path
