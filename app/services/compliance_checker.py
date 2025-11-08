"""
Compliance Checker - Validates content against FTC guidelines and affiliate marketing regulations
Ensures all generated content meets legal and ethical standards
"""
from typing import Dict, Any, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """Checks content compliance with FTC guidelines and affiliate marketing regulations"""
    
    # FTC-required disclosure patterns
    DISCLOSURE_PATTERNS = [
        r'affiliate\s+link',
        r'affiliate\s+disclosure',
        r'earn\s+commission',
        r'compensated\s+for',
        r'paid\s+partnership',
        r'sponsored\s+content',
        r'#ad\b',
        r'#sponsored\b',
        r'#affiliate\b'
    ]
    
    # Prohibited claims (health, income, etc.)
    PROHIBITED_CLAIMS = {
        'health': [
            r'cure\s+\w+',
            r'treat\s+\w+\s+disease',
            r'guaranteed\s+weight\s+loss',
            r'miracle\s+cure',
            r'FDA\s+approved\s+for',
            r'clinically\s+proven\s+to\s+cure'
        ],
        'income': [
            r'guaranteed\s+income',
            r'get\s+rich\s+quick',
            r'make\s+\$\d+\s+overnight',
            r'no\s+work\s+required',
            r'passive\s+income\s+guaranteed',
            r'earn\s+\$\d+\s+per\s+day\s+guaranteed'
        ],
        'results': [
            r'guaranteed\s+results',
            r'works\s+for\s+everyone',
            r'100%\s+success\s+rate',
            r'no\s+risk',
            r'instant\s+results\s+guaranteed'
        ]
    }
    
    # Exaggerated language patterns
    EXAGGERATION_PATTERNS = [
        r'\b(best|greatest|perfect|ultimate|revolutionary)\s+ever\b',
        r'\b(never|always|everyone|nobody|impossible)\b',
        r'\b(amazing|incredible|unbelievable|miraculous)\b.*\b(results|transformation)\b',
        r'change\s+your\s+life\s+forever',
        r'too\s+good\s+to\s+be\s+true'
    ]
    
    # Required elements for different content types
    REQUIRED_ELEMENTS = {
        'review_article': ['disclosure', 'balanced_view'],
        'landing_page': ['disclosure', 'disclaimer'],
        'email_sequence': ['disclosure', 'unsubscribe'],
        'social_media': ['disclosure_hashtag'],
        'comparison': ['disclosure', 'balanced_view']
    }
    
    def check_content(
        self,
        content: str,
        content_type: str,
        product_category: Optional[str] = None,
        is_product_description: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive compliance check for generated content

        Args:
            content: Content to check
            content_type: Type of content
            product_category: Optional product category (health, finance, etc.)
            is_product_description: If True, skips disclosure/disclaimer checks
                                   (product descriptions don't need affiliate disclosures)

        Returns:
            Compliance report with score and issues
        """
        try:
            issues = []
            warnings = []
            score = 100  # Start with perfect score

            # Check for affiliate disclosure (SKIP for product descriptions)
            if not is_product_description:
                disclosure_check = self._check_disclosure(content, content_type)
                if not disclosure_check['compliant']:
                    issues.append({
                        'severity': 'critical',
                        'type': 'missing_disclosure',
                        'message': disclosure_check['message'],
                        'suggestion': disclosure_check['suggestion']
                    })
                    score -= 30

            # Check for prohibited claims (ALWAYS check)
            prohibited_check = self._check_prohibited_claims(content, product_category)
            if prohibited_check['violations']:
                for violation in prohibited_check['violations']:
                    issues.append({
                        'severity': 'critical',
                        'type': 'prohibited_claim',
                        'message': violation['message'],
                        'location': violation['location'],
                        'suggestion': violation['suggestion']
                    })
                    score -= 20

            # Check for exaggerated language (ALWAYS check)
            exaggeration_check = self._check_exaggerations(content)
            if exaggeration_check['found']:
                for exaggeration in exaggeration_check['instances']:
                    warnings.append({
                        'severity': 'medium',
                        'type': 'exaggerated_language',
                        'message': f"Potentially exaggerated claim: '{exaggeration}'",
                        'suggestion': 'Consider using more measured language'
                    })
                    score -= 5

            # Check for required elements (SKIP for product descriptions)
            if not is_product_description:
                required_check = self._check_required_elements(content, content_type)
                if required_check['missing']:
                    for missing in required_check['missing']:
                        issues.append({
                            'severity': 'high',
                            'type': 'missing_element',
                            'message': f"Missing required element: {missing}",
                            'suggestion': required_check['suggestions'].get(missing, '')
                        })
                        score -= 15
            
            # Check for misleading statements
            misleading_check = self._check_misleading_statements(content)
            if misleading_check['found']:
                for statement in misleading_check['statements']:
                    warnings.append({
                        'severity': 'medium',
                        'type': 'potentially_misleading',
                        'message': statement['message'],
                        'suggestion': statement['suggestion']
                    })
                    score -= 10
            
            # Ensure score doesn't go below 0
            score = max(0, score)
            
            # Determine compliance status
            if score >= 90:
                status = 'compliant'
            elif score >= 70:
                status = 'needs_review'
            else:
                status = 'non_compliant'
            
            return {
                'compliant': status == 'compliant',
                'status': status,
                'score': score,
                'issues': issues,
                'warnings': warnings,
                'summary': self._generate_summary(status, score, issues, warnings)
            }
            
        except Exception as e:
            logger.error(f"Error checking compliance: {str(e)}")
            return {
                'compliant': False,
                'status': 'error',
                'score': 0,
                'issues': [{
                    'severity': 'critical',
                    'type': 'check_error',
                    'message': f"Error during compliance check: {str(e)}"
                }],
                'warnings': []
            }
    
    def _check_disclosure(self, content: str, content_type: str) -> Dict[str, Any]:
        """Check for proper affiliate disclosure"""
        
        content_lower = content.lower()
        
        # Check if any disclosure pattern is present
        has_disclosure = any(
            re.search(pattern, content_lower)
            for pattern in self.DISCLOSURE_PATTERNS
        )
        
        if has_disclosure:
            # Check if disclosure is prominent (in first 500 characters for articles)
            if content_type in ['review_article', 'landing_page', 'tutorial']:
                first_section = content[:500].lower()
                prominent = any(
                    re.search(pattern, first_section)
                    for pattern in self.DISCLOSURE_PATTERNS
                )
                
                if not prominent:
                    return {
                        'compliant': False,
                        'message': 'Affiliate disclosure found but not prominently placed',
                        'suggestion': 'Move disclosure to the beginning of the content (within first paragraph)'
                    }
            
            return {
                'compliant': True,
                'message': 'Proper affiliate disclosure found'
            }
        
        return {
            'compliant': False,
            'message': 'No affiliate disclosure found',
            'suggestion': self._get_disclosure_template(content_type)
        }
    
    def _check_prohibited_claims(
        self,
        content: str,
        product_category: Optional[str]
    ) -> Dict[str, Any]:
        """Check for prohibited claims based on product category"""
        
        violations = []
        content_lower = content.lower()
        
        # Check all prohibited claim categories
        for category, patterns in self.PROHIBITED_CLAIMS.items():
            # Focus on health claims if it's a health product
            if product_category == 'health' or category != 'health':
                for pattern in patterns:
                    matches = re.finditer(pattern, content_lower, re.IGNORECASE)
                    for match in matches:
                        violations.append({
                            'category': category,
                            'message': f"Prohibited {category} claim detected",
                            'location': match.group(),
                            'suggestion': self._get_claim_alternative(category, match.group())
                        })
        
        return {
            'violations': violations,
            'count': len(violations)
        }
    
    def _check_exaggerations(self, content: str) -> Dict[str, Any]:
        """Check for exaggerated language"""
        
        instances = []
        
        for pattern in self.EXAGGERATION_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                instances.append(match.group())
        
        return {
            'found': len(instances) > 0,
            'instances': instances,
            'count': len(instances)
        }
    
    def _check_required_elements(
        self,
        content: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Check for required elements based on content type"""
        
        required = self.REQUIRED_ELEMENTS.get(content_type, [])
        missing = []
        suggestions = {}
        
        content_lower = content.lower()
        
        for element in required:
            if element == 'disclosure':
                has_disclosure = any(
                    re.search(pattern, content_lower)
                    for pattern in self.DISCLOSURE_PATTERNS
                )
                if not has_disclosure:
                    missing.append('disclosure')
                    suggestions['disclosure'] = self._get_disclosure_template(content_type)
            
            elif element == 'balanced_view':
                # Check for both positive and consideration/limitation mentions
                has_pros = bool(re.search(r'(benefit|advantage|pro|strength)', content_lower))
                has_cons = bool(re.search(r'(limitation|drawback|con|consideration|however)', content_lower))
                
                if not (has_pros and has_cons):
                    missing.append('balanced_view')
                    suggestions['balanced_view'] = 'Include both benefits and potential limitations for a balanced review'
            
            elif element == 'disclaimer':
                has_disclaimer = bool(re.search(r'(disclaimer|results may vary|individual results)', content_lower))
                if not has_disclaimer:
                    missing.append('disclaimer')
                    suggestions['disclaimer'] = 'Add a disclaimer about individual results varying'
            
            elif element == 'unsubscribe':
                has_unsubscribe = bool(re.search(r'unsubscribe', content_lower))
                if not has_unsubscribe:
                    missing.append('unsubscribe')
                    suggestions['unsubscribe'] = 'Include unsubscribe information in email footer'
            
            elif element == 'disclosure_hashtag':
                has_hashtag = bool(re.search(r'#(ad|sponsored|affiliate)', content_lower))
                if not has_hashtag:
                    missing.append('disclosure_hashtag')
                    suggestions['disclosure_hashtag'] = 'Add #ad, #sponsored, or #affiliate hashtag'
        
        return {
            'missing': missing,
            'suggestions': suggestions
        }
    
    def _check_misleading_statements(self, content: str) -> Dict[str, Any]:
        """Check for potentially misleading statements"""
        
        statements = []
        content_lower = content.lower()
        
        # Check for absolute statements without qualifiers
        absolute_patterns = [
            (r'will\s+definitely', 'Consider using "may" or "can" instead of absolute terms'),
            (r'always\s+works', 'Avoid absolute claims; use "often works" or "typically works"'),
            (r'never\s+fails', 'Avoid absolute claims; acknowledge potential limitations'),
            (r'guaranteed\s+to', 'Remove guarantee language unless backed by actual guarantee policy')
        ]
        
        for pattern, suggestion in absolute_patterns:
            if re.search(pattern, content_lower):
                statements.append({
                    'message': f"Potentially misleading absolute statement found",
                    'suggestion': suggestion
                })
        
        return {
            'found': len(statements) > 0,
            'statements': statements
        }
    
    def _get_disclosure_template(self, content_type: str) -> str:
        """Get appropriate disclosure template for content type"""
        
        templates = {
            'review_article': "Add at the beginning: 'Disclosure: This article contains affiliate links. If you make a purchase through these links, I may earn a commission at no additional cost to you.'",
            'landing_page': "Add prominently: 'Affiliate Disclosure: This page contains affiliate links. We may earn a commission if you make a purchase.'",
            'email_sequence': "Add to footer: 'This email contains affiliate links. I may earn a commission from purchases made through these links.'",
            'social_media': "Add hashtag: #ad or #affiliate at the beginning of the post",
            'comparison': "Add at the beginning: 'Disclosure: This comparison includes affiliate links. I may earn a commission from qualifying purchases.'"
        }
        
        return templates.get(content_type, "Add clear affiliate disclosure at the beginning of the content")
    
    def _get_claim_alternative(self, category: str, claim: str) -> str:
        """Get alternative phrasing for prohibited claims"""
        
        alternatives = {
            'health': "Instead of making medical claims, describe the product's intended use and suggest consulting a healthcare professional",
            'income': "Instead of guaranteeing income, share realistic examples and emphasize that results vary based on effort",
            'results': "Instead of guaranteeing results, use phrases like 'may help', 'designed to', or 'intended to support'"
        }
        
        return alternatives.get(category, "Rephrase to avoid absolute or guaranteed claims")
    
    def _generate_summary(
        self,
        status: str,
        score: int,
        issues: List[Dict],
        warnings: List[Dict]
    ) -> str:
        """Generate a human-readable summary of compliance check"""
        
        if status == 'compliant':
            return f"Content is compliant with affiliate marketing regulations (Score: {score}/100). {len(warnings)} minor warnings to review."
        elif status == 'needs_review':
            return f"Content needs review before publication (Score: {score}/100). Found {len(issues)} issues and {len(warnings)} warnings."
        else:
            return f"Content is non-compliant and requires significant revisions (Score: {score}/100). Found {len(issues)} critical issues."
    
    def suggest_improvements(self, compliance_report: Dict[str, Any]) -> List[str]:
        """
        Generate actionable improvement suggestions based on compliance report
        
        Args:
            compliance_report: Report from check_content()
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Prioritize critical issues
        critical_issues = [
            issue for issue in compliance_report.get('issues', [])
            if issue.get('severity') == 'critical'
        ]
        
        for issue in critical_issues:
            if issue.get('suggestion'):
                suggestions.append(f"🔴 CRITICAL: {issue['suggestion']}")
        
        # Add high-priority issues
        high_issues = [
            issue for issue in compliance_report.get('issues', [])
            if issue.get('severity') == 'high'
        ]
        
        for issue in high_issues:
            if issue.get('suggestion'):
                suggestions.append(f"🟡 HIGH: {issue['suggestion']}")
        
        # Add warnings
        for warning in compliance_report.get('warnings', [])[:3]:  # Limit to top 3
            if warning.get('suggestion'):
                suggestions.append(f"⚠️ WARNING: {warning['suggestion']}")
        
        return suggestions