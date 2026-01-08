#!/usr/bin/env python3
"""
Economy Context Service for FXSentinel
Provides economy data (central bank rates, economic indicators) from static JSON
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EconomyContextService:
    """Service for providing economy context data from static JSON"""
    
    def __init__(self):
        self.json_path = Path(__file__).parent.parent.parent / 'src' / 'data' / 'economyIndicators.json'
        self.cache = None
        self.cache_timestamp = None
        self.cache_duration = 3600  # Cache for 1 hour (economy data changes monthly/quarterly)
    
    def _load_static_json(self) -> Optional[Dict]:
        """Load economy indicators from static JSON file"""
        try:
            # Check cache first
            if self._is_cache_valid():
                logger.debug("Using cached economy data")
                return self.cache
            
            if not self.json_path.exists():
                logger.warning(f"Economy indicators JSON not found: {self.json_path}")
                return None
            
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cache the data
            self.cache = data
            self.cache_timestamp = datetime.now()
            
            logger.info(f"✅ Loaded economy data from {self.json_path}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in economy indicators file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading economy indicators: {e}")
            return None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self.cache is None or self.cache_timestamp is None:
            return False
        
        age_seconds = (datetime.now() - self.cache_timestamp).total_seconds()
        return age_seconds < self.cache_duration
    
    def _map_currency_to_country_code(self, currency: str) -> str:
        """Map currency code to country code in JSON"""
        currency_map = {
            'USD': 'US',
            'EUR': 'EUR',
            'GBP': 'GBP',
            'JPY': 'JPY'
        }
        return currency_map.get(currency.upper(), currency.upper())
    
    def get_economy_context(self, currency: str) -> Optional[Dict]:
        """
        Get economy context for a currency
        
        Args:
            currency: Currency code (USD, EUR, GBP, JPY)
        
        Returns:
            Dict with central bank rate and indicators, or None if not available
            {
                'currency': 'USD',
                'central_bank_rate': {
                    'value': 3.75,
                    'trend': 'down',
                    'bank_name': 'Fed',
                    'as_of': '2025-12-10'
                },
                'indicators': {
                    'interest-rate': {...},
                    'inflation-YoY': {...},
                    ...
                }
            }
        """
        try:
            # Load JSON data
            json_data = self._load_static_json()
            if not json_data:
                return None
            
            # Map currency to country code
            country_code = self._map_currency_to_country_code(currency)
            
            if country_code not in json_data:
                logger.warning(f"No economy data found for currency {currency} (country code: {country_code})")
                return None
            
            country_data = json_data[country_code]
            
            # Extract central bank rates
            central_bank_rate = None
            if 'centralBankRates' in country_data:
                cbr_data = country_data['centralBankRates']
                central_bank_rate = {
                    'value': cbr_data.get('rate'),
                    'trend': cbr_data.get('trend', 'stable'),
                    'bank_name': cbr_data.get('bankName', ''),
                    'as_of': cbr_data.get('asOf', '')
                }
            
            # Extract indicators
            indicators = country_data.get('indicators', {})
            
            return {
                'currency': currency.upper(),
                'country_code': country_code,
                'central_bank_rate': central_bank_rate,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"Error getting economy context for {currency}: {e}")
            return None
    
    def get_indicator_by_id(self, currency: str, indicator_id: str) -> Optional[Dict]:
        """Get a specific indicator by ID for a currency"""
        economy_context = self.get_economy_context(currency)
        if not economy_context:
            return None
        
        indicators = economy_context.get('indicators', {})
        return indicators.get(indicator_id)
    
    def get_central_bank_rate(self, currency: str) -> Optional[Dict]:
        """Get central bank rate for a currency"""
        economy_context = self.get_economy_context(currency)
        if not economy_context:
            return None
        
        return economy_context.get('central_bank_rate')

# Global instance
economy_context_service = EconomyContextService()

