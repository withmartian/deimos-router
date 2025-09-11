"""Code detection rule implementation."""

import re
from typing import Any, Dict
from .base import Rule, Decision


class CodeRule(Rule):
    """Rule that makes decisions based on whether the request contains code."""
    
    def __init__(self, name: str, code: str, not_code: str):
        """Initialize a CodeRule.
        
        Args:
            name: The name of this rule
            code: Model name or rule name (deimos/rules/rule-name) to use when code is detected
            not_code: Model name or rule name (deimos/rules/rule-name) to use when no code is detected
        """
        super().__init__(name)
        self.code = code
        self.not_code = not_code
        
        # Compile regex patterns for code detection
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for detecting code."""
        # Programming language keywords and constructs
        self.code_patterns = [
            # Function definitions and calls
            re.compile(r'\b(?:def|function|func|fn)\s+\w+\s*\(', re.IGNORECASE),
            re.compile(r'\w+\s*\([^)]*\)\s*\{', re.IGNORECASE),  # function() {
            re.compile(r'\w+\([^)]*\)\s*:', re.IGNORECASE),  # function():
            
            # Control structures
            re.compile(r'\b(?:if|else|elif|while|for|switch|case|try|catch|finally|with)\s*\(', re.IGNORECASE),
            re.compile(r'\b(?:if|else|elif|while|for|switch|case|try|catch|finally|with)\s+', re.IGNORECASE),
            
            # Variable declarations and assignments
            re.compile(r'\b(?:var|let|const|int|string|bool|float|double|char|long|short)\s+\w+', re.IGNORECASE),
            re.compile(r'\w+\s*=\s*(?:new\s+)?\w+\(', re.IGNORECASE),
            re.compile(r'\w+\s*:\s*\w+\s*=', re.IGNORECASE),  # Go-style declarations
            
            # Class and object definitions
            re.compile(r'\b(?:class|struct|interface|enum|type)\s+\w+', re.IGNORECASE),
            re.compile(r'\b(?:public|private|protected|static|final|abstract)\s+', re.IGNORECASE),
            
            # Import/include statements
            re.compile(r'\b(?:import|from|include|require|using|#include)\s+', re.IGNORECASE),
            re.compile(r'from\s+\w+\s+import', re.IGNORECASE),
            
            # Common programming operators and syntax
            re.compile(r'[=!<>]=|[+\-*/%]=|\+\+|--|&&|\|\||<<|>>', re.IGNORECASE),
            re.compile(r'=>|->|\.\.\.|::', re.IGNORECASE),
            
            # Code blocks and brackets
            re.compile(r'{\s*$', re.MULTILINE),  # Opening brace on its own line
            re.compile(r'^\s*}', re.MULTILINE),  # Closing brace on its own line
            re.compile(r'^\s*\w+\s*\([^)]*\)\s*{', re.MULTILINE),  # Function with brace
            
            # Common programming patterns
            re.compile(r'\breturn\s+(?:\w+|["\'].*["\']|null|true|false|None|\d+)', re.IGNORECASE),
            re.compile(r'\bprint\s*\(|console\.log\s*\(|System\.out\.print', re.IGNORECASE),
            re.compile(r'\bthrow\s+new\s+\w+|raise\s+\w+', re.IGNORECASE),
            
            # SQL patterns (stronger patterns for better detection)
            re.compile(r'\bSELECT\s+.*\s+FROM\s+\w+', re.IGNORECASE),
            re.compile(r'\bINSERT\s+INTO\s+\w+', re.IGNORECASE),
            re.compile(r'\bUPDATE\s+\w+\s+SET\s+', re.IGNORECASE),
            re.compile(r'\bDELETE\s+FROM\s+\w+', re.IGNORECASE),
            re.compile(r'\bCREATE\s+TABLE\s+\w+', re.IGNORECASE),
            re.compile(r'\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|FROM|WHERE|JOIN|GROUP BY|ORDER BY)\b', re.IGNORECASE),
            
            # HTML/XML tags (basic detection)
            re.compile(r'<\/?[a-zA-Z][^>]*>', re.IGNORECASE),
            re.compile(r'<\w+[^>]*\/>', re.IGNORECASE),  # Self-closing tags
            
            # JSON patterns
            re.compile(r'{\s*["\']?\w+["\']?\s*:\s*["\']?[^,}]+["\']?', re.IGNORECASE),
            
            # Command line patterns
            re.compile(r'^\s*[$#]\s+\w+', re.MULTILINE),  # Shell prompts
            re.compile(r'\b(?:cd|ls|mkdir|rm|cp|mv|grep|awk|sed|curl|wget|git|npm|pip|docker)\s+', re.IGNORECASE),
            
            # Configuration file patterns
            re.compile(r'^\s*\w+\s*=\s*["\']?[^"\'\n]+["\']?$', re.MULTILINE),
            re.compile(r'^\s*\[\w+\]', re.MULTILINE),  # INI sections
            
            # Code comments
            re.compile(r'//.*$|/\*.*?\*/|#.*$|<!--.*?-->', re.MULTILINE | re.DOTALL),
            
            # Indentation patterns (common in Python, YAML, etc.)
            re.compile(r'^\s{4,}\w+|^\t+\w+', re.MULTILINE),  # 4+ spaces or tabs
            
            # Error messages and stack traces
            re.compile(r'\b(?:Error|Exception|Traceback|at\s+\w+\.\w+)', re.IGNORECASE),
            re.compile(r'File\s+"[^"]+",\s+line\s+\d+', re.IGNORECASE),
            
            # Version control patterns
            re.compile(r'\b(?:commit|branch|merge|pull|push|clone)\s+\w+', re.IGNORECASE),
            
            # Package manager patterns
            re.compile(r'\b(?:npm\s+install|pip\s+install|composer\s+install|gem\s+install)', re.IGNORECASE),
        ]
        
        # Patterns that indicate NOT code (to reduce false positives)
        self.not_code_patterns = [
            # Natural language patterns
            re.compile(r'\b(?:the|and|or|but|however|therefore|because|although|while|during|after|before|since|until|unless|if|when|where|why|how|what|who|which|that|this|these|those|some|many|few|several|all|most|each|every|any|no|none|both|either|neither)\b', re.IGNORECASE),
            
            # Question patterns
            re.compile(r'\?.*(?:how|what|why|when|where|who|which|can|could|would|should|will|do|does|did|is|are|was|were)', re.IGNORECASE),
            re.compile(r'(?:how|what|why|when|where|who|which|can|could|would|should|will|do|does|did|is|are|was|were).*\?', re.IGNORECASE),
            
            # Conversational patterns
            re.compile(r'\b(?:please|thank|thanks|hello|hi|hey|goodbye|bye|sorry|excuse|help|assist|explain|describe|tell|show|give|provide)\b', re.IGNORECASE),
        ]
    
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate based on whether the request contains code.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Decision based on code detection
        """
        # Extract text content from messages
        text_content = self._extract_text_content(request_data)
        
        if not text_content:
            return Decision(self.not_code, trigger="no_content")
        
        # Check if content contains code
        if self._contains_code(text_content):
            return Decision(self.code, trigger="code_detected")
        else:
            return Decision(self.not_code, trigger="no_code_detected")
    
    def _extract_text_content(self, request_data: Dict[str, Any]) -> str:
        """Extract text content from request messages.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Combined text content from all messages
        """
        messages = request_data.get('messages', [])
        text_parts = []
        
        for message in messages:
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                if isinstance(content, str):
                    text_parts.append(content)
        
        return '\n'.join(text_parts)
    
    def _contains_code(self, text: str) -> bool:
        """Determine if text contains code using regex patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if code is detected, False otherwise
        """
        # Count matches for code patterns
        code_matches = 0
        for pattern in self.code_patterns:
            matches = len(pattern.findall(text))
            code_matches += matches
        
        # Count matches for not-code patterns
        not_code_matches = 0
        for pattern in self.not_code_patterns:
            matches = len(pattern.findall(text))
            not_code_matches += matches
        
        # Decision logic: code is detected if:
        # 1. There are code matches AND
        # 2. Code matches significantly outnumber natural language matches OR
        # 3. There are strong code indicators (multiple matches)
        
        if code_matches == 0:
            return False
        
        # Strong code indicators (need more matches for high confidence)
        if code_matches >= 4:
            return True
        
        # If there are many natural language indicators, be more conservative
        if not_code_matches >= 5 and code_matches < 3:
            return False
        
        # Ratio-based decision - need higher threshold
        if not_code_matches == 0:
            return code_matches >= 2  # Need at least 2 code matches if no natural language
        
        # Code matches should be at least 50% of total matches to be considered code
        total_matches = code_matches + not_code_matches
        code_ratio = code_matches / total_matches
        
        return code_ratio >= 0.5 and code_matches >= 2
    
    def __repr__(self) -> str:
        return f"CodeRule(name='{self.name}', code={self.code}, not_code={self.not_code})"
