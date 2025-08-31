#!/usr/bin/env python3
"""
Data Validation Service for FXSentinel
Ensures only real, accurate economic data is sent to GPT analysis
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class EconomicDataValidator:
    """Validates economic event data for accuracy and completeness"""
    
    def __init__(self):
        self.valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']
        self.valid_impact_levels = ['high', 'medium', 'low']
        
        # Economic indicator patterns for validation
        self.economic_indicators = {
            'employment': ['non-farm payrolls', 'nfp', 'employment', 'unemployment', 'adp', 'jobless claims'],
            'inflation': ['cpi', 'consumer price index', 'ppi', 'producer price index', 'inflation'],
            'growth': ['gdp', 'gross domestic product', 'retail sales', 'industrial production'],
            'central_bank': ['interest rate', 'fomc', 'ecb', 'boe', 'boj', 'rba', 'boc', 'snb', 'rbnz'],
            'manufacturing': ['pmi', 'manufacturing', 'ism', 'industrial'],
            'housing': ['housing', 'home sales', 'building permits', 'construction']
        }
    
    def validate_event_data(self, event: Dict) -> Tuple[bool, Dict, List[str]]:
        """
        Comprehensive validation of economic event data
        
        Returns:
            (is_valid, validated_event, validation_errors)
        """
        validation_errors = []
        validated_event = event.copy()
        
        # 1. Basic field validation
        if not self._validate_basic_fields(event, validation_errors):
            return False, validated_event, validation_errors
        
        # 2. Date and time validation
        if not self._validate_date_time(event, validated_event, validation_errors):
            return False, validated_event, validation_errors
        
        # 3. Economic data validation
        if not self._validate_economic_data(event, validated_event, validation_errors):
            return False, validated_event, validation_errors
        
        # 4. Currency and impact validation
        if not self._validate_currency_impact(event, validated_event, validation_errors):
            return False, validated_event, validation_errors
        
        # 5. Data consistency validation
        if not self._validate_data_consistency(validated_event, validation_errors):
            return False, validated_event, validation_errors
        
        # 6. Mock data detection
        if self._is_mock_data(event):
            validation_errors.append("Event appears to be mock/fallback data - not suitable for analysis")
            return False, validated_event, validation_errors
        
        return True, validated_event, validation_errors
    
    def _validate_basic_fields(self, event: Dict, errors: List[str]) -> bool:
        """Validate basic required fields"""
        required_fields = ['title', 'currency', 'impact']
        
        for field in required_fields:
            if not event.get(field):
                errors.append(f"Missing required field: {field}")
                return False
        
        if len(event.get('title', '').strip()) < 3:
            errors.append("Event title too short or empty")
            return False
        
        return True
    
    def _validate_date_time(self, event: Dict, validated_event: Dict, errors: List[str]) -> bool:
        """Validate and normalize date/time information"""
        date = event.get('date', '')
        time = event.get('time', '')
        
        # Extract year from title if missing from date
        year = self._extract_year_from_title(event.get('title', ''))
        
        if date:
            # Check if date contains year
            if not re.search(r'\b(20[0-9]{2})\b', date):
                if year:
                    # Add year to date
                    validated_event['date'] = f"{date} {year}"
                    validated_event['year'] = year
                else:
                    # Try to extract year from other sources
                    year = self._extract_year_from_context(event)
                    if year:
                        validated_event['date'] = f"{date} {year}"
                        validated_event['year'] = year
                    else:
                        errors.append("Cannot determine event year - date may be invalid")
                        return False
        
        # Validate time format
        if time and time != 'TBD':
            if not re.match(r'^\d{1,2}:\d{2}', time):
                errors.append(f"Invalid time format: {time}")
                return False
        
        return True
    
    def _validate_economic_data(self, event: Dict, validated_event: Dict, errors: List[str]) -> bool:
        """Validate economic data values"""
        previous = event.get('previous', '')
        expected = event.get('expected', '')
        actual = event.get('actual', '')
        
        # Validate previous value
        if previous and previous not in ['--', 'N/A', '']:
            if not self._is_valid_economic_value(previous, event.get('title', '')):
                errors.append(f"Invalid previous value: {previous}")
                return False
        
        # Validate expected value
        if expected and expected not in ['--', 'N/A', '']:
            if not self._is_valid_economic_value(expected, event.get('title', '')):
                errors.append(f"Invalid expected value: {expected}")
                return False
        
        # Validate actual value
        if actual and actual not in ['--', 'N/A', '']:
            if not self._is_valid_economic_value(actual, event.get('title', '')):
                errors.append(f"Invalid actual value: {actual}")
                return False
        
        return True
    
    def _validate_currency_impact(self, event: Dict, validated_event: Dict, errors: List[str]) -> bool:
        """Validate currency and impact level"""
        currency = event.get('currency', '').upper()
        impact = event.get('impact', '').lower()
        
        if currency not in self.valid_currencies:
            errors.append(f"Invalid currency: {currency}")
            return False
        
        if impact not in self.valid_impact_levels:
            errors.append(f"Invalid impact level: {impact}")
            return False
        
        return True
    
    def _validate_data_consistency(self, event: Dict, errors: List[str]) -> bool:
        """Validate data consistency and logic"""
        previous = event.get('previous', '')
        expected = event.get('expected', '')
        actual = event.get('actual', '')
        
        # Check for contradictory data
        if actual and actual not in ['--', 'N/A', '']:
            # If we have actual data, this should be a post-event analysis
            if expected and expected not in ['--', 'N/A', '']:
                # Validate that expected and actual are in reasonable range
                if not self._are_values_consistent(expected, actual, event.get('title', '')):
                    errors.append("Expected and actual values appear inconsistent")
                    return False
        
        return True
    
    def _is_mock_data(self, event: Dict) -> bool:
        """Detect if event data is mock/fallback data"""
        title = event.get('title', '').lower()
        
        # Check for mock data indicators
        mock_indicators = [
            'us unemployment rate',  # Common mock title
            'test event',
            'mock',
            'fallback',
            'sample'
        ]
        
        for indicator in mock_indicators:
            if indicator in title:
                return True
        
        # Check for suspicious data patterns
        if event.get('source') == 'fallback_data':
            return True
        
        # Check for unrealistic economic values
        if self._has_unrealistic_values(event):
            return True
        
        return False
    
    def _extract_year_from_title(self, title: str) -> Optional[str]:
        """Extract year from event title"""
        year_match = re.search(r'\b(20[0-9]{2})\b', title)
        return year_match.group(1) if year_match else None
    
    def _extract_year_from_context(self, event: Dict) -> Optional[str]:
        """Extract year from event context"""
        # Check if event has a timestamp
        timestamp = event.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return str(dt.year)
            except:
                pass
        
        # Default to current year if no year found
        return str(datetime.now().year)
    
    def _is_valid_economic_value(self, value: str, event_title: str) -> bool:
        """Validate if economic value is reasonable for the event type"""
        if not value or value in ['--', 'N/A', '']:
            return True
        
        try:
            # Remove common suffixes
            clean_value = re.sub(r'[%KMBT]', '', str(value))
            num_value = float(clean_value)
            
            # Validate based on event type
            title_lower = event_title.lower()
            
            # Employment events (NFP, ADP, etc.)
            if any(keyword in title_lower for keyword in ['employment', 'payroll', 'jobs', 'non-farm', 'nfp']):
                return 0 <= num_value <= 2000  # Reasonable employment range
            
            # Percentage events (CPI, GDP, etc.)
            elif any(keyword in title_lower for keyword in ['cpi', 'inflation', 'gdp', 'rate', 'unemployment']):
                return -50 <= num_value <= 100  # Reasonable percentage range
            
            # Index events (PMI, etc.)
            elif any(keyword in title_lower for keyword in ['pmi', 'index', 'manufacturing']):
                return 0 <= num_value <= 100  # PMI range
            
            # Default validation
            return -1000 <= num_value <= 10000
            
        except (ValueError, TypeError):
            return False
    
    def _are_values_consistent(self, expected: str, actual: str, event_title: str) -> bool:
        """Check if expected and actual values are reasonably consistent"""
        try:
            exp_clean = re.sub(r'[%KMBT]', '', str(expected))
            act_clean = re.sub(r'[%KMBT]', '', str(actual))
            
            exp_val = float(exp_clean)
            act_val = float(act_clean)
            
            # Calculate percentage difference
            if exp_val != 0:
                diff_percent = abs(act_val - exp_val) / abs(exp_val) * 100
                return diff_percent <= 200  # Allow up to 200% difference
            
            return True
            
        except (ValueError, TypeError, ZeroDivisionError):
            return True  # If we can't compare, assume consistent
    
    def _has_unrealistic_values(self, event: Dict) -> bool:
        """Check for unrealistic economic values"""
        title = event.get('title', '').lower()
        
        # Check for obviously wrong values
        for field in ['previous', 'expected', 'actual']:
            value = event.get(field, '')
            if value and value not in ['--', 'N/A', '']:
                try:
                    clean_value = re.sub(r'[%KMBT]', '', str(value))
                    num_value = float(clean_value)
                    
                    # Employment events with wrong units
                    if any(keyword in title for keyword in ['employment', 'payroll', 'jobs', 'non-farm', 'nfp']):
                        if num_value > 100 and '%' not in str(value):
                            # Employment numbers should be in thousands or millions
                            if num_value < 1000:  # Too small for employment
                                return True
                    
                    # Percentage events with wrong values
                    elif any(keyword in title for keyword in ['cpi', 'inflation', 'gdp', 'rate', 'unemployment']):
                        if num_value > 1000:  # Unrealistic percentage
                            return True
                    
                except (ValueError, TypeError):
                    pass
        
        return False
    
    def get_validation_summary(self, event: Dict, is_valid: bool, errors: List[str]) -> Dict:
        """Generate validation summary for logging"""
        return {
            'event_title': event.get('title', 'Unknown'),
            'event_id': event.get('id', 'Unknown'),
            'is_valid': is_valid,
            'validation_errors': errors,
            'data_quality': 'high' if is_valid and not errors else 'low',
            'recommendation': 'use_for_analysis' if is_valid else 'reject_data',
            'timestamp': datetime.now().isoformat()
        }

# Global instance
economic_data_validator = EconomicDataValidator()
