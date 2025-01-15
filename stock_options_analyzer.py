import requests
import pandas as pd
from datetime import datetime
import time
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlphaVantageAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_pause = 12  # AlphaVantage has a rate limit of 5 calls per minute for free tier

    def _make_request(self, params: Dict[str, Any]) -> Dict:
        """Make a request to the AlphaVantage API with rate limiting."""
        try:
            params['apikey'] = self.api_key
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            time.sleep(self.rate_limit_pause)  # Rate limiting
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def fetch_stock_data(self, symbol: str, interval: str = 'daily', outputsize: str = 'full') -> pd.DataFrame:
        """Fetch historical stock price data."""
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        
        # Extract time series data
        time_series = data.get(f'Time Series ({interval.capitalize()})', {})
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.index = pd.to_datetime(df.index)
        
        # Rename columns
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Convert string values to float
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        return df

    def fetch_options_data(self, symbol: str, date: str = None) -> pd.DataFrame:
        """Fetch options chain data."""
        params = {
            'function': 'HISTORICAL_OPTIONS',
            'symbol': symbol
        }
        
        if date:
            params['date'] = date
            
        data = self._make_request(params)
        
        # Extract options data
        options_data = data.get('options', [])
        
        if not options_data:
            logger.warning(f"No options data found for {symbol}")
            return pd.DataFrame()
            
        # Convert to DataFrame
        df = pd.DataFrame(options_data)
        
        # Convert numeric columns
        numeric_columns = ['strike', 'premium', 'openInterest', 'impliedVolatility']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])
                
        return df

def calculate_greeks(options_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate option Greeks using the provided implied volatility.
    Note: This is a simplified calculation. For more accurate Greeks,
    consider using the QuantLib library.
    """
    # Basic Greeks calculation
    options_df['delta'] = options_df['impliedVolatility'].apply(
        lambda x: x * 0.4 if x else None)  # Simplified delta calculation
    options_df['gamma'] = options_df['impliedVolatility'].apply(
        lambda x: x * 0.2 if x else None)  # Simplified gamma calculation
    options_df['theta'] = options_df['impliedVolatility'].apply(
        lambda x: -x * 0.1 if x else None)  # Simplified theta calculation
    options_df['vega'] = options_df['impliedVolatility'].apply(
        lambda x: x * 0.3 if x else None)  # Simplified vega calculation
    
    return options_df

def main():
    # Replace with your API key
    API_KEY = "YOUR_API_KEY"
    SYMBOL = "IBM"
    
    try:
        api = AlphaVantageAPI(API_KEY)
        
        # Fetch stock data
        logger.info(f"Fetching stock data for {SYMBOL}")
        stock_df = api.fetch_stock_data(SYMBOL)
        stock_df.to_csv('stock_data.csv')
        logger.info("Stock data saved to stock_data.csv")
        
        # Fetch options data
        logger.info(f"Fetching options data for {SYMBOL}")
        options_df = api.fetch_options_data(SYMBOL)
        
        # Calculate Greeks
        if not options_df.empty:
            options_df = calculate_greeks(options_df)
            options_df.to_csv('options_data.csv', index=False)
            logger.info("Options data saved to options_data.csv")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 