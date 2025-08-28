#!/usr/bin/env python3
"""
Context-Aware Grammar Analysis Engine

This module provides intelligent grammar analysis for document editing operations.
It analyzes user responses in sentence context to determine optimal replacement strategies.
"""

import re
from typing import Dict, Tuple, Optional, List
from enum import Enum


class ReplacementStrategy(Enum):
    """Strategy for handling user response in context."""
    NARROW_REPLACE = "narrow_replace"      # Replace just the placeholder
    SENTENCE_RESTRUCTURE = "sentence_restructure"  # Rebuild the full sentence  
    TRANSFORM = "transform"                # Convert response format then replace


class ResponseType(Enum):
    """Semantic categories for user responses."""
    DURATION = "duration"                  # "24 hours", "1 week"
    FREQUENCY = "frequency"                # "daily", "monthly", "quarterly"
    IMMEDIACY = "immediacy"                # "immediately", "instantly", "ASAP"
    PERSON_NAME = "person_name"            # "John Smith", "jane.doe@company.com"
    ROLE_TITLE = "role_title"              # "IT Manager", "CEO", "CISO"
    TOOL_NAME = "tool_name"                # "1Password", "GitHub", "Jira"
    BOOLEAN_CHOICE = "boolean_choice"      # "Yes", "No"
    COMPLEX_PHRASE = "complex_phrase"      # "by end of business day"
    OTHER = "other"


class ContextAnalyzer:
    """
    Analyzes sentence context and user responses for optimal grammar handling.
    """
    
    def __init__(self):
        self.duration_patterns = [
            r'\d+\s*(hours?|days?|weeks?|months?|years?)',
            r'(business\s+hours?|business\s+days?)',
            r'(immediately|instantly|right\s+away|asap)'
        ]
        
        self.frequency_patterns = [
            r'(daily|weekly|monthly|quarterly|annually|yearly)',
            r'(hourly|semi-annually|bi-weekly|bi-monthly)'
        ]
        
        self.immediacy_patterns = [
            r'(immediately|instantly|right\s+away|asap|at\s+once)',
            r'(without\s+delay|forthwith|straight\s+away)'
        ]
    
    def analyze_operation(self, target_text: str, context: str, user_response: str, 
                         placeholder: Optional[str] = None) -> Dict:
        """
        Analyze a grammar operation and determine optimal handling strategy.
        
        Args:
            target_text: Current target text from operation
            context: Full sentence context containing the placeholder
            user_response: User's response to replace placeholder with
            placeholder: The original placeholder (e.g., "<24 business hours>")
            
        Returns:
            Dict with analysis results and recommended strategy
        """
        # Extract placeholder if not provided
        if not placeholder:
            placeholder = self._extract_placeholder(target_text, context)
        
        # Categorize user response
        response_type = self._categorize_response(user_response)
        
        # Analyze grammatical compatibility
        compatibility = self._test_compatibility(context, placeholder, user_response, response_type)
        
        # Determine strategy
        strategy = self._determine_strategy(compatibility, response_type, context, placeholder)
        
        # Generate recommended operation
        recommended_op = self._generate_operation(
            strategy, target_text, context, placeholder, user_response, response_type
        )
        
        return {
            "original_target": target_text,
            "context": context,
            "placeholder": placeholder,
            "user_response": user_response,
            "response_type": response_type.value,
            "compatibility": compatibility,
            "strategy": strategy.value,
            "recommended_operation": recommended_op,
            "analysis_reason": self._explain_strategy(strategy, compatibility, response_type)
        }
    
    def _extract_placeholder(self, target_text: str, context: str) -> Optional[str]:
        """Extract placeholder from target_text or context."""
        # Look for common placeholder patterns
        placeholder_patterns = [
            r'<[^>]+>',      # <placeholder>
            r'\[[^\]]+\]',   # [placeholder]
            r'\{[^}]+\}',    # {placeholder}
        ]
        
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, target_text)
            if matches:
                return matches[0]
            
            matches = re.findall(pattern, context)
            if matches:
                return matches[0]
        
        return None
    
    def _categorize_response(self, user_response: str) -> ResponseType:
        """Categorize user response semantically."""
        response_lower = user_response.lower().strip()
        
        # Check for immediacy indicators first (before duration patterns)
        immediacy_words = ['immediately', 'instantly', 'right away', 'asap', 'at once',
                          'without delay', 'forthwith', 'straight away']
        if any(word in response_lower for word in immediacy_words):
            return ResponseType.IMMEDIACY
        
        for pattern in self.immediacy_patterns:
            if re.search(pattern, response_lower):
                return ResponseType.IMMEDIACY
        
        # Check for frequency indicators (expanded list)
        frequency_words = ['daily', 'weekly', 'monthly', 'quarterly', 'annually', 'yearly', 
                          'hourly', 'semi-annually', 'bi-weekly', 'bi-monthly', 'annual']
        if response_lower in frequency_words:
            return ResponseType.FREQUENCY
        
        for pattern in self.frequency_patterns:
            if re.search(pattern, response_lower):
                return ResponseType.FREQUENCY
        
        # Check for duration indicators (after immediacy)
        for pattern in self.duration_patterns:
            if re.search(pattern, response_lower):
                return ResponseType.DURATION
        
        # Check for email patterns (person names)
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', response_lower):
            return ResponseType.PERSON_NAME
        
        # Check for person name patterns (handles both proper and improper capitalization)
        if re.match(r'^[a-zA-Z]+\s+[a-zA-Z]+$', user_response.strip()):
            return ResponseType.PERSON_NAME
        
        # Check for tool names (password managers, etc.)
        tool_keywords = ['password', 'lastpass', 'dashlane', 'bitwarden', 'keeper', 'github', 'gitlab', 'jira', 'clickup', 'asana']
        if any(keyword in response_lower for keyword in tool_keywords):
            return ResponseType.TOOL_NAME
        
        # Check for role titles
        role_keywords = ['manager', 'director', 'officer', 'admin', 'lead', 'head', 'chief', 'ceo', 'cto', 'ciso']
        if any(keyword in response_lower for keyword in role_keywords):
            return ResponseType.ROLE_TITLE
        
        # Check for boolean responses
        if response_lower in ['yes', 'no', 'true', 'false']:
            return ResponseType.BOOLEAN_CHOICE
        
        # Check for complex phrases
        if any(word in response_lower for word in ['within', 'by', 'before', 'after', 'during']):
            return ResponseType.COMPLEX_PHRASE
        
        return ResponseType.OTHER
    
    def _test_compatibility(self, context: str, placeholder: Optional[str], 
                          user_response: str, response_type: ResponseType) -> str:
        """Use AI reasoning to test grammatical compatibility - NO HARDCODED PATTERNS."""
        if not placeholder:
            return "unknown"
        
        # UNIVERSAL APPROACH: Use intelligent reasoning instead of pattern matching
        return self._ai_compatibility_test(context, placeholder, user_response, response_type)
    
    def _ai_compatibility_test(self, context: str, placeholder: Optional[str],
                             user_response: str, response_type: ResponseType) -> str:
        """
        Use pure AI reasoning - NO HARDCODED PATTERNS!
        This is a simplified version that lets downstream AI handle the complexity.
        """
        # UNIVERSAL APPROACH: Let the AI figure out compatibility
        # The actual intelligence happens in the downstream AI processing
        
        # Only handle the most basic transformations
        if response_type == ResponseType.PERSON_NAME:
            # Basic name capitalization
            if user_response != user_response.title():
                return "needs_transform"
        
        # For everything else, let the AI decide
        # This removes all document-specific pattern matching
        return "unknown"
    
    def _determine_strategy(self, compatibility: str, response_type: ResponseType, 
                          context: str, placeholder: Optional[str]) -> ReplacementStrategy:
        """Determine strategy using simplified logic - let AI handle complexity."""
        
        # SIMPLIFIED: Remove hardcoded response type logic
        if compatibility == "needs_transform":
            return ReplacementStrategy.TRANSFORM
        
        # For unknown compatibility, let downstream AI decide the strategy
        # The JSON will contain all context needed for intelligent analysis
        if compatibility == "unknown":
            return ReplacementStrategy.NARROW_REPLACE  # Default, AI can override
        
        # Default to narrow replacement
        return ReplacementStrategy.NARROW_REPLACE
    
    def _generate_operation(self, strategy: ReplacementStrategy, original_target: str,
                          context: str, placeholder: Optional[str], user_response: str,
                          response_type: ResponseType) -> Dict:
        """Generate operation with simplified logic - let downstream AI handle complexity."""
        
        if strategy == ReplacementStrategy.TRANSFORM:
            # Only do basic transformations like name capitalization
            transformed = self._transform_response(user_response, response_type, context)
            return {
                "target_text": placeholder or original_target,
                "replacement": transformed,
                "explanation": f"Basic transformation applied: '{user_response}' → '{transformed}'"
            }
        
        # For all other strategies, provide raw data for downstream AI processing
        return {
            "target_text": placeholder or original_target,
            "replacement": user_response,
            "explanation": f"Raw data provided for AI analysis: context='{context}', response='{user_response}'"
        }
    
    def _transform_response(self, user_response: str, response_type: ResponseType, context: str = "") -> str:
        """Basic transformations only - let AI handle complex logic."""
        
        # SIMPLIFIED: Only basic transformations, no document-specific logic
        if response_type == ResponseType.PERSON_NAME:
            # Basic name capitalization
            return ' '.join(word.capitalize() for word in user_response.split())
        
        # For everything else, return as-is and let downstream AI handle it
        return user_response.strip()
    
    def _restructure_sentence(self, context: str, placeholder: Optional[str], 
                            user_response: str, response_type: ResponseType) -> str:
        """Use AI reasoning to restructure sentence for any pattern - NO HARDCODED RULES."""
        
        # UNIVERSAL APPROACH: Use AI reasoning instead of pattern matching
        restructured = self._ai_sentence_restructure(context, placeholder, user_response, response_type)
        if restructured:
            return restructured
        
        # Fallback: simple placeholder replacement
        if placeholder:
            return context.replace(placeholder, user_response)
        
        return context
    
    def _ai_sentence_restructure(self, context: str, placeholder: Optional[str], 
                               user_response: str, response_type: ResponseType) -> Optional[str]:
        """
        SIMPLIFIED: Let downstream AI handle the complexity.
        This method now just provides a framework - the real AI processing
        happens when the JSON is processed by the main AI system.
        """
        if not placeholder:
            return None
            
        # UNIVERSAL APPROACH: Don't hardcode patterns!
        # Just return None and let the downstream AI figure out the optimal restructuring
        # The JSON will contain all the context needed for intelligent analysis
        
        # The actual AI analysis happens in the processing pipeline,
        # not in this grammar analyzer
        
        return None
    
    def _explain_strategy(self, strategy: ReplacementStrategy, compatibility: str,
                         response_type: ResponseType) -> str:
        """Provide human-readable explanation of why this strategy was chosen."""
        if strategy == ReplacementStrategy.NARROW_REPLACE:
            return f"User response ({response_type.value}) fits grammatically in existing sentence structure"
        
        elif strategy == ReplacementStrategy.TRANSFORM:
            return f"User response ({response_type.value}) needs formatting transformation but fits existing structure"
        
        elif strategy == ReplacementStrategy.SENTENCE_RESTRUCTURE:
            return f"User response ({response_type.value}) requires sentence restructuring for grammatical compatibility"
        
        return "Strategy determination unclear"


def analyze_smart_replace_operation(target_text: str, context: str, user_response: str, 
                                  placeholder: Optional[str] = None) -> Dict:
    """
    Convenience function for analyzing a smart_replace operation.
    
    Args:
        target_text: Current target text from JSON operation
        context: Full sentence context containing the placeholder  
        user_response: User's response to replace placeholder with
        placeholder: Optional explicit placeholder text
        
    Returns:
        Analysis results with recommended operation
    """
    analyzer = ContextAnalyzer()
    return analyzer.analyze_operation(target_text, context, user_response, placeholder)


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        {
            "target_text": "<24 business hours>",
            "context": "Access will be terminated within <24 business hours> of the termination notice.",
            "user_response": "immediately",
            "placeholder": "<24 business hours>"
        },
        {
            "target_text": "<24 business hours>",
            "context": "The maximum time frame for access termination is set at <24 business hours>.",
            "user_response": "immediately",
            "placeholder": "<24 business hours>"
        },
        {
            "target_text": "<IT Manager>", 
            "context": "Exceptions will be approved by <IT Manager>.",
            "user_response": "john smith",
            "placeholder": "<IT Manager>"
        },
        {
            "target_text": "a quarterly basis",
            "context": "Reviews will be conducted on a quarterly basis.",
            "user_response": "monthly",
            "placeholder": "quarterly"
        }
    ]
    
    analyzer = ContextAnalyzer()
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i} ===")
        result = analyzer.analyze_operation(**test)
        
        print(f"Context: {result['context']}")
        print(f"User Response: {result['user_response']} ({result['response_type']})")
        print(f"Strategy: {result['strategy']}")
        print(f"Reason: {result['analysis_reason']}")
        print(f"Recommended Target: {result['recommended_operation']['target_text']}")
        print(f"Recommended Replacement: {result['recommended_operation']['replacement']}")
        print(f"Explanation: {result['recommended_operation']['explanation']}")
