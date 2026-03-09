import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LetterBoxdLoader:
    """Load and process Letterboxd export CSV data"""
    
    EXPECTED_COLUMNS = [
        'Name', 'Year', 'Letterboxd URI', 'Rating', 'Watched Date', 'Review'
    ]
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.raw_df = None
        
    def load(self) -> pd.DataFrame:
        """Load and preprocess CSV file"""
        try:
            self.raw_df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded raw data with shape: {self.raw_df.shape}")
            logger.info(f"Columns: {list(self.raw_df.columns)}")
            
            self.df = self.raw_df.copy()
            self._preprocess()
            
            logger.info(f"Preprocessed data with shape: {self.df.shape}")
            return self.df
            
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise ValueError(f"Error loading CSV: {e}")
    
    def _preprocess(self):
        """Clean and prepare data for RAG"""
        # Handle missing values
        self.df = self.df.fillna("")
        
        # Standardize column names
        self.df.columns = [col.strip() for col in self.df.columns]
        
        # Create combined text field for embeddings
        text_fields = []
        for col in ['Name', 'Year', 'Review']:
            if col in self.df.columns:
                text_fields.append(col)
        
        if text_fields:
            self.df['combined_text'] = self.df[text_fields].astype(str).agg(
                ' '.join, axis=1
            )
        else:
            self.df['combined_text'] = self.df.astype(str).agg(
                ' '.join, axis=1
            )
        
        # Remove duplicates
        self.df = self.df.drop_duplicates(subset=['Name'], keep='first')
        
        logger.info(f"Data preprocessed. Final count: {len(self.df)} unique movies")
    
    def get_movies(self) -> List[Dict]:
        """Return movies as list of dictionaries"""
        if self.df is None:
            raise ValueError("Data not loaded. Call load() first.")
        return self.df.to_dict('records')
    
    def get_stats(self) -> Dict:
        """Get statistics about the dataset"""
        return {
            'total_movies': len(self.df),
            'columns': list(self.df.columns),
            'years_range': f"{self.df['Year'].min()} - {self.df['Year'].max()}" if 'Year' in self.df.columns else "N/A",
            'rated_movies': len(self.df[self.df['Rating'] != '']) if 'Rating' in self.df.columns else 0,
        }