"""Code language detection rule implementation."""

import re
from typing import Any, Dict, List, Optional, Union
import openai
from ..config import config
from .base import Rule, Decision


class CodeLanguageRule(Rule):
    """Rule that makes decisions based on the specific programming language detected."""
    
    def __init__(self, name: str, language_mappings: Dict[str, Union[str, Rule]], 
                 default: Optional[Union[str, Rule]] = None,
                 llm_model: Optional[str] = None,
                 enable_llm_fallback: bool = True):
        """Initialize a CodeLanguageRule.
        
        Args:
            name: The name of this rule
            language_mappings: Dictionary mapping language names to models or rules
            default: Default model/rule when no language is detected or mapped
            llm_model: Model to use for LLM-based language detection fallback.
                      If None, uses the default model from config.
            enable_llm_fallback: Whether to use LLM fallback for unmapped languages
        """
        super().__init__(name)
        self.language_mappings = language_mappings
        self.default = default
        self.llm_model = llm_model or config.get_default_model('code_language_detection')
        self.enable_llm_fallback = enable_llm_fallback
        
        # Compile regex patterns for language detection
        self._compile_language_patterns()
    
    def _compile_language_patterns(self) -> None:
        """Compile regex patterns for detecting specific programming languages."""
        
        # Language-specific patterns with scoring weights
        self.language_patterns = {
            'python': [
                (re.compile(r'\bdef\s+\w+\s*\([^)]*\)\s*:', re.IGNORECASE), 3),
                (re.compile(r'\bimport\s+\w+|from\s+\w+\s+import', re.IGNORECASE), 2),
                (re.compile(r'\bif\s+__name__\s*==\s*["\']__main__["\']', re.IGNORECASE), 4),
                (re.compile(r'\bclass\s+\w+\s*\([^)]*\)\s*:', re.IGNORECASE), 3),
                (re.compile(r'\belif\b|\bexcept\b|\bfinally\b', re.IGNORECASE), 2),
                (re.compile(r'^\s{4}\w+|^\s{4}#', re.MULTILINE), 1),  # 4-space indentation
                (re.compile(r'\bprint\s*\(|\blen\s*\(|\brange\s*\(', re.IGNORECASE), 1),
                (re.compile(r'\.py\b|python\b', re.IGNORECASE), 1),
            ],
            
            'javascript': [
                (re.compile(r'\bfunction\s+\w+\s*\([^)]*\)\s*\{', re.IGNORECASE), 3),
                (re.compile(r'\b(?:const|let|var)\s+\w+\s*=', re.IGNORECASE), 2),
                (re.compile(r'=>|\.then\s*\(|\.catch\s*\(', re.IGNORECASE), 2),
                (re.compile(r'\bconsole\.log\s*\(|\balert\s*\(', re.IGNORECASE), 2),
                (re.compile(r'\b(?:async|await)\b', re.IGNORECASE), 2),
                (re.compile(r'\brequire\s*\(|import\s+.*\s+from', re.IGNORECASE), 2),
                (re.compile(r'\.js\b|javascript\b|node\.js', re.IGNORECASE), 1),
                (re.compile(r'\$\{.*\}|`.*`', re.IGNORECASE), 1),  # Template literals
            ],
            
            'java': [
                (re.compile(r'\bpublic\s+(?:static\s+)?(?:void|int|String)\s+\w+\s*\(', re.IGNORECASE), 4),
                (re.compile(r'\bclass\s+\w+\s*(?:extends\s+\w+)?\s*\{', re.IGNORECASE), 3),
                (re.compile(r'\bpublic\s+static\s+void\s+main\s*\(', re.IGNORECASE), 4),
                (re.compile(r'\bSystem\.out\.print', re.IGNORECASE), 3),
                (re.compile(r'\bimport\s+java\.', re.IGNORECASE), 3),
                (re.compile(r'\b(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?\w+', re.IGNORECASE), 2),
                (re.compile(r'\.java\b', re.IGNORECASE), 1),
                (re.compile(r'\bnew\s+\w+\s*\(', re.IGNORECASE), 1),
            ],
            
            'cpp': [
                (re.compile(r'#include\s*<[^>]+>|#include\s*"[^"]+"', re.IGNORECASE), 3),
                (re.compile(r'\bint\s+main\s*\([^)]*\)\s*\{', re.IGNORECASE), 4),
                (re.compile(r'\bstd::|using\s+namespace\s+std', re.IGNORECASE), 3),
                (re.compile(r'\bcout\s*<<|\bcin\s*>>', re.IGNORECASE), 3),
                (re.compile(r'\b(?:public|private|protected)\s*:', re.IGNORECASE), 2),
                (re.compile(r'\bclass\s+\w+\s*(?::\s*(?:public|private|protected)\s+\w+)?\s*\{', re.IGNORECASE), 2),
                (re.compile(r'\.cpp\b|\.hpp\b|\.h\b|c\+\+', re.IGNORECASE), 1),
                (re.compile(r'\bdelete\s+\w+|\bnew\s+\w+', re.IGNORECASE), 1),
            ],
            
            'c': [
                (re.compile(r'#include\s*<[^>]+\.h>', re.IGNORECASE), 3),
                (re.compile(r'\bint\s+main\s*\([^)]*\)\s*\{', re.IGNORECASE), 3),
                (re.compile(r'\bprintf\s*\(|\bscanf\s*\(', re.IGNORECASE), 3),
                (re.compile(r'\bmalloc\s*\(|\bfree\s*\(', re.IGNORECASE), 2),
                (re.compile(r'\bstruct\s+\w+\s*\{', re.IGNORECASE), 2),
                (re.compile(r'\.c\b(?!pp)', re.IGNORECASE), 1),
                (re.compile(r'\btypedef\s+(?:struct\s+)?\w+', re.IGNORECASE), 1),
            ],
            
            'csharp': [
                (re.compile(r'\busing\s+System', re.IGNORECASE), 4),  # Higher weight for C# specific
                (re.compile(r'\bnamespace\s+\w+\s*\{', re.IGNORECASE), 4),  # Higher weight for namespace
                (re.compile(r'\bConsole\.WriteLine\s*\(', re.IGNORECASE), 4),  # Higher weight for C# specific
                (re.compile(r'\bpublic\s+(?:static\s+)?(?:void|int|string)\s+\w+\s*\(', re.IGNORECASE), 2),  # Lower weight since shared with Java
                (re.compile(r'\bpublic\s+class\s+\w+', re.IGNORECASE), 1),  # Lower weight since shared with Java
                (re.compile(r'\.cs\b|C#', re.IGNORECASE), 2),
                (re.compile(r'\bvar\s+\w+\s*=|\bstring\s+\w+', re.IGNORECASE), 2),
                (re.compile(r'\bConsole\.Write\s*\(|\bConsole\.Read', re.IGNORECASE), 3),  # More C# specific patterns
            ],
            
            'php': [
                (re.compile(r'<\?php', re.IGNORECASE), 4),
                (re.compile(r'\$\w+\s*=', re.IGNORECASE), 3),
                (re.compile(r'\bfunction\s+\w+\s*\([^)]*\)\s*\{', re.IGNORECASE), 2),
                (re.compile(r'\becho\s+|\bprint\s+', re.IGNORECASE), 2),
                (re.compile(r'\brequire\s+|\binclude\s+', re.IGNORECASE), 2),
                (re.compile(r'\.php\b', re.IGNORECASE), 1),
                (re.compile(r'->\w+|\$this->', re.IGNORECASE), 1),
            ],
            
            'ruby': [
                (re.compile(r'\bdef\s+\w+(?:\([^)]*\))?\s*$', re.MULTILINE | re.IGNORECASE), 3),
                (re.compile(r'\bclass\s+\w+(?:\s*<\s*\w+)?\s*$', re.MULTILINE | re.IGNORECASE), 3),
                (re.compile(r'\bend\s*$', re.MULTILINE | re.IGNORECASE), 2),
                (re.compile(r'\bputs\s+|\bp\s+', re.IGNORECASE), 2),
                (re.compile(r'\brequire\s+["\']|\bgem\s+["\']', re.IGNORECASE), 2),
                (re.compile(r'\.rb\b|ruby', re.IGNORECASE), 1),
                (re.compile(r'@\w+|@@\w+', re.IGNORECASE), 1),  # Instance/class variables
            ],
            
            'go': [
                (re.compile(r'\bpackage\s+\w+', re.IGNORECASE), 3),
                (re.compile(r'\bfunc\s+\w+\s*\([^)]*\)', re.IGNORECASE), 3),
                (re.compile(r'\bimport\s*\(|\bimport\s+"', re.IGNORECASE), 2),
                (re.compile(r'\bfmt\.Print|\bfmt\.Sprintf', re.IGNORECASE), 3),
                (re.compile(r':=|\bvar\s+\w+\s+\w+', re.IGNORECASE), 2),
                (re.compile(r'\.go\b|golang', re.IGNORECASE), 1),
                (re.compile(r'\bgo\s+func\s*\(', re.IGNORECASE), 2),  # Goroutines
            ],
            
            'rust': [
                (re.compile(r'\bfn\s+\w+\s*\([^)]*\)', re.IGNORECASE), 4),  # Higher weight for fn
                (re.compile(r'\buse\s+\w+::', re.IGNORECASE), 3),  # Higher weight for use statements
                (re.compile(r'\blet\s+(?:mut\s+)?\w+\s*=', re.IGNORECASE), 2),
                (re.compile(r'\bprintln!\s*\(|\bpanic!\s*\(', re.IGNORECASE), 4),  # Higher weight for macros
                (re.compile(r'\bmatch\s+\w+\s*\{', re.IGNORECASE), 3),  # Higher weight for match
                (re.compile(r'\.rs\b|rust', re.IGNORECASE), 1),
                (re.compile(r'\bimpl\s+\w+|\btrait\s+\w+', re.IGNORECASE), 3),  # Higher weight
                (re.compile(r'\b(?:u8|u16|u32|u64|i8|i16|i32|i64|f32|f64|usize|isize)\b', re.IGNORECASE), 2),  # Rust types
                (re.compile(r'\b_\s*=>', re.IGNORECASE), 3),  # Rust match arm with underscore
            ],
            
            'swift': [
                (re.compile(r'\bfunc\s+\w+\s*\([^)]*\)', re.IGNORECASE), 3),
                (re.compile(r'\bimport\s+(?:Foundation|UIKit|SwiftUI)', re.IGNORECASE), 3),
                (re.compile(r'\bvar\s+\w+\s*:\s*\w+|\blet\s+\w+\s*:\s*\w+', re.IGNORECASE), 2),
                (re.compile(r'\bprint\s*\(', re.IGNORECASE), 2),
                (re.compile(r'\bclass\s+\w+\s*:\s*\w+', re.IGNORECASE), 2),
                (re.compile(r'\.swift\b|swift', re.IGNORECASE), 1),
                (re.compile(r'\bguard\s+|\bdefer\s+', re.IGNORECASE), 2),
            ],
            
            'kotlin': [
                (re.compile(r'\bfun\s+\w+\s*\([^)]*\)', re.IGNORECASE), 3),
                (re.compile(r'\bclass\s+\w+(?:\s*:\s*\w+)?\s*\{', re.IGNORECASE), 2),
                (re.compile(r'\bval\s+\w+\s*=|\bvar\s+\w+\s*=', re.IGNORECASE), 2),
                (re.compile(r'\bprintln\s*\(', re.IGNORECASE), 2),
                (re.compile(r'\bimport\s+\w+(?:\.\w+)*', re.IGNORECASE), 1),
                (re.compile(r'\.kt\b|kotlin', re.IGNORECASE), 1),
                (re.compile(r'\bwhen\s*\(|\bdata\s+class', re.IGNORECASE), 2),
            ],
        }
        
        # SQL patterns (more comprehensive)
        self.language_patterns['sql'] = [
            (re.compile(r'\bSELECT\s+.*\s+FROM\s+\w+', re.IGNORECASE), 4),
            (re.compile(r'\bINSERT\s+INTO\s+\w+', re.IGNORECASE), 3),
            (re.compile(r'\bUPDATE\s+\w+\s+SET\s+', re.IGNORECASE), 3),
            (re.compile(r'\bDELETE\s+FROM\s+\w+', re.IGNORECASE), 3),
            (re.compile(r'\bCREATE\s+TABLE\s+\w+', re.IGNORECASE), 3),
            (re.compile(r'\bJOIN\s+\w+\s+ON\s+', re.IGNORECASE), 2),
            (re.compile(r'\bWHERE\s+\w+\s*[=<>]', re.IGNORECASE), 2),
            (re.compile(r'\bGROUP\s+BY\s+|\bORDER\s+BY\s+', re.IGNORECASE), 2),
        ]
        
        # HTML patterns
        self.language_patterns['html'] = [
            (re.compile(r'<!DOCTYPE\s+html>', re.IGNORECASE), 4),
            (re.compile(r'<html[^>]*>|</html>', re.IGNORECASE), 3),
            (re.compile(r'<head[^>]*>|</head>|<body[^>]*>|</body>', re.IGNORECASE), 3),
            (re.compile(r'<(?:div|span|p|h[1-6]|a|img|ul|ol|li|form|input|button|table|tr|td|th)[^>]*>', re.IGNORECASE), 2),
            (re.compile(r'<\w+[^>]*\s+(?:class|id|src|href|action|method|type|name)\s*=', re.IGNORECASE), 2),
            (re.compile(r'</(?:div|span|p|h[1-6]|a|form|button|table|tr|td|th)>', re.IGNORECASE), 1),
            (re.compile(r'\.html?\b', re.IGNORECASE), 1),
        ]
        
        # CSS patterns (more specific to avoid false matches with other languages)
        self.language_patterns['css'] = [
            (re.compile(r'[.#]\w+\s*\{[^}]*(?:color|background|margin|padding|border|font|width|height)[^}]*\}', re.IGNORECASE), 4),  # CSS with properties
            (re.compile(r'\w+\s*\{\s*(?:color|background|margin|padding|border|font|width|height|display|position)', re.IGNORECASE), 3),  # CSS properties
            (re.compile(r'@media\s+|\b@import\s+|\b@keyframes\s+', re.IGNORECASE), 4),
            (re.compile(r':\s*(?:hover|active|focus|before|after|nth-child|first-child|last-child)', re.IGNORECASE), 3),
            (re.compile(r'\.css\b', re.IGNORECASE), 1),
            (re.compile(r'(?:px|em|rem|%|vh|vw|pt)\s*[;}]', re.IGNORECASE), 2),  # CSS units
        ]
    
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate based on the specific programming language detected.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Decision based on detected language
        """
        # Extract text content from messages
        text_content = self._extract_text_content(request_data)
        
        if not text_content:
            return Decision(self.default)
        
        # Try regex-based detection first
        detected_language = self._detect_language_regex(text_content)
        
        if detected_language and detected_language in self.language_mappings:
            return Decision(self.language_mappings[detected_language])
        
        # If no regex match and LLM fallback is enabled, try LLM detection
        if self.enable_llm_fallback and self.language_mappings:
            # Get unmapped languages that could be detected by LLM
            unmapped_languages = [lang for lang in self.language_mappings.keys() 
                                if lang not in self.language_patterns]
            
            if unmapped_languages:
                llm_detected = self._detect_language_llm(text_content, unmapped_languages)
                if llm_detected and llm_detected in self.language_mappings:
                    return Decision(self.language_mappings[llm_detected])
        
        # Fall back to default
        return Decision(self.default)
    
    def _extract_text_content(self, request_data: Dict[str, Any]) -> str:
        """Extract text content from request messages."""
        messages = request_data.get('messages', [])
        text_parts = []
        
        for message in messages:
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                if isinstance(content, str):
                    text_parts.append(content)
        
        return '\n'.join(text_parts)
    
    def _detect_language_regex(self, text: str) -> Optional[str]:
        """Detect programming language using regex patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language name or None
        """
        language_scores = {}
        
        # Score each language based on pattern matches
        for language, patterns in self.language_patterns.items():
            score = 0
            for pattern, weight in patterns:
                matches = len(pattern.findall(text))
                score += matches * weight
            
            if score > 0:
                language_scores[language] = score
        
        if not language_scores:
            return None
        
        # Find the maximum score
        max_score = max(language_scores.values())
        
        # Minimum score threshold to avoid weak matches
        if max_score < 3:
            return None
        
        # Get all languages with the maximum score
        best_languages = [lang for lang, score in language_scores.items() if score == max_score]
        
        # If there's only one best language, return it
        if len(best_languages) == 1:
            return best_languages[0]
        
        # Handle ties by prioritizing certain languages
        # Priority order: SQL > HTML > CSS > others (alphabetical)
        priority_order = ['sql', 'html', 'css']
        
        for priority_lang in priority_order:
            if priority_lang in best_languages:
                return priority_lang
        
        # If no priority language found, return the first alphabetically
        return sorted(best_languages)[0]
    
    def _detect_language_llm(self, text: str, candidate_languages: List[str]) -> Optional[str]:
        """Detect programming language using LLM fallback.
        
        Args:
            text: Text to analyze
            candidate_languages: List of possible languages to choose from
            
        Returns:
            Detected language name or None
        """
        try:
            # Get credentials for the LLM
            if not config.is_configured():
                return None
            
            credentials = config.get_credentials()
            
            # Create OpenAI client
            client = openai.OpenAI(
                api_key=credentials['api_key'],
                base_url=credentials.get('api_url')
            )
            
            # Create prompt for language detection
            languages_list = ', '.join(candidate_languages)
            prompt = f"""Analyze the following code snippet and determine which programming language it is most likely written in.

You must choose from one of these languages: {languages_list}

If the code doesn't clearly match any of these languages, respond with "None".

Respond with ONLY the language name (or "None"), nothing else.

Code to analyze:
```
{text[:2000]}  # Limit text to avoid token limits
```"""

            # Make the API call
            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            # Extract the response
            detected = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            if detected == "none":
                return None
            
            # Check if the detected language is in our candidate list
            for lang in candidate_languages:
                if lang.lower() == detected:
                    return lang
            
            return None
            
        except Exception:
            # If LLM detection fails, return None
            return None
    
    def __repr__(self) -> str:
        return f"CodeLanguageRule(name='{self.name}', languages={list(self.language_mappings.keys())})"
