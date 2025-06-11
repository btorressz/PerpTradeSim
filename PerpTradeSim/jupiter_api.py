import requests
import time
from typing import Optional, Dict, Any
import logging

class JupiterAPI:
    """Jupiter API client for fetching SOL/USDC price data"""
    
    def __init__(self):
        self.base_url = "https://quote-api.jup.ag/v6"
        self.sol_mint = "So11111111111111111111111111111111111111112"  # SOL mint address
        self.usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC mint address
        self.session = requests.Session()
        
    def get_quote(self, input_mint: str, output_mint: str, amount: int = 1000000) -> Optional[Dict[Any, Any]]:
        """
        Get quote from Jupiter API
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address  
            amount: Amount in smallest unit (default 1 SOL = 1,000,000 lamports)
            
        Returns:
            Quote data or None if error
        """
        try:
            url = f"{self.base_url}/quote"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": 50  # 0.5% slippage
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Jupiter API error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in get_quote: {e}")
            return None
    
    def get_sol_usdc_price(self) -> Optional[float]:
        """
        Get current SOL/USDC price
        
        Returns:
            Price as float or None if error
        """
        quote_data = self.get_quote(self.sol_mint, self.usdc_mint)
        
        if not quote_data:
            return None
            
        try:
            # Calculate price from quote
            input_amount = int(quote_data["inAmount"])
            output_amount = int(quote_data["outAmount"])
            
            # Convert from lamports/micro-units to actual tokens
            # SOL has 9 decimals, USDC has 6 decimals
            sol_amount = input_amount / 1e9
            usdc_amount = output_amount / 1e6
            
            price = usdc_amount / sol_amount
            return round(price, 4)
            
        except (KeyError, ValueError, ZeroDivisionError) as e:
            logging.error(f"Error parsing quote data: {e}")
            logging.error(f"Quote data received: {quote_data}")
            return None
    
    def get_price_with_retry(self, max_retries: int = 3) -> Optional[float]:
        """
        Get price with retry logic
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            Price or None if all retries failed
        """
        for attempt in range(max_retries):
            price = self.get_sol_usdc_price()
            if price is not None:
                return price
                
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait 1 second before retry
                
        return None
