"""
Prompt Builder - Constructs optimized prompts for AI content generation
Handles different content types and marketing angles
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds optimized prompts for various content types"""
    
    # Content type templates
    TEMPLATES = {
        'review_article': {
            'system': """You are an expert affiliate marketer and content writer specializing in honest, detailed product reviews. 
Your reviews are balanced, informative, and help readers make informed purchasing decisions.
You focus on real benefits, potential drawbacks, and practical use cases.""",
            'structure': [
                'engaging_introduction',
                'product_overview',
                'key_features_analysis',
                'benefits_and_results',
                'potential_drawbacks',
                'who_its_for',
                'pricing_and_value',
                'final_verdict'
            ]
        },
        'comparison': {
            'system': """You are an expert at creating fair, detailed product comparisons that help readers choose the best option for their needs.
You analyze products objectively across multiple criteria and provide clear recommendations.""",
            'structure': [
                'introduction',
                'comparison_criteria',
                'side_by_side_analysis',
                'pros_and_cons',
                'use_case_scenarios',
                'recommendation'
            ]
        },
        'tutorial': {
            'system': """You are an expert educator who creates clear, actionable tutorials that help users get results quickly.
Your tutorials are step-by-step, beginner-friendly, and include practical tips.""",
            'structure': [
                'introduction',
                'prerequisites',
                'step_by_step_guide',
                'tips_and_best_practices',
                'common_mistakes',
                'conclusion'
            ]
        },
        'landing_page': {
            'system': """You are an expert copywriter specializing in high-converting landing pages.
You understand persuasion psychology, benefit-driven copy, and clear calls-to-action.""",
            'structure': [
                'headline',
                'subheadline',
                'problem_agitation',
                'solution_introduction',
                'benefits_list',
                'social_proof',
                'cta_primary',
                'features_section',
                'faq',
                'cta_final'
            ]
        },
        'email_sequence': {
            'system': """You are an expert email marketer who creates engaging, conversion-focused email sequences.
Your emails build trust, provide value, and guide subscribers toward a purchase decision.""",
            'structure': [
                'welcome_email',
                'value_email',
                'story_email',
                'objection_handling',
                'urgency_email',
                'final_offer'
            ]
        },
        'social_media': {
            'system': """You are a social media marketing expert who creates engaging, shareable content that drives traffic and conversions.
You understand platform-specific best practices and audience engagement.""",
            'structure': [
                'hook',
                'value_proposition',
                'call_to_action',
                'hashtags'
            ]
        },
        'video_script': {
            'system': """You are an expert video script writer who creates engaging, persuasive video content.
Your scripts are conversational, benefit-focused, and optimized for viewer retention.""",
            'structure': [
                'hook',
                'introduction',
                'main_content',
                'demonstration',
                'call_to_action',
                'outro'
            ]
        }
    }
    
    def build_prompt(
        self,
        content_type: str,
        product_info: Dict[str, Any],
        marketing_angle: str,
        tone: str = 'professional',
        additional_context: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        email_sequence_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Build a complete prompt for content generation

        Args:
            content_type: Type of content to generate
            product_info: Product information dictionary
            marketing_angle: Marketing angle to use
            tone: Desired tone (professional, casual, enthusiastic, etc.)
            additional_context: Additional context from RAG
            constraints: Content constraints (word count, keywords, etc.)
            email_sequence_config: Email sequence configuration (num_emails, sequence_type)

        Returns:
            Dictionary with system and user prompts
        """
        try:
            template = self.TEMPLATES.get(content_type)

            if not template:
                # Fallback to generic template
                template = {
                    'system': "You are an expert content writer and affiliate marketer.",
                    'structure': ['introduction', 'main_content', 'conclusion']
                }

            # Build system prompt
            system_prompt = self._build_system_prompt(
                template['system'],
                tone,
                constraints
            )

            # Build user prompt
            user_prompt = self._build_user_prompt(
                content_type=content_type,
                structure=template['structure'],
                product_info=product_info,
                marketing_angle=marketing_angle,
                additional_context=additional_context,
                constraints=constraints,
                email_sequence_config=email_sequence_config
            )

            return {
                'system': system_prompt,
                'user': user_prompt,
                'content_type': content_type,
                'marketing_angle': marketing_angle
            }

        except Exception as e:
            logger.error(f"Error building prompt: {str(e)}")
            raise
    
    def _build_system_prompt(
        self,
        base_system: str,
        tone: str,
        constraints: Optional[Dict[str, Any]]
    ) -> str:
        """Build the system prompt with tone and constraints"""
        
        tone_instructions = {
            'professional': "Maintain a professional, authoritative tone. Be informative and trustworthy.",
            'casual': "Use a friendly, conversational tone. Be approachable and relatable.",
            'enthusiastic': "Be energetic and passionate. Show genuine excitement about the product.",
            'educational': "Be clear, patient, and thorough. Focus on teaching and explaining.",
            'persuasive': "Be compelling and convincing. Focus on benefits and transformation."
        }
        
        system_prompt = f"""{base_system}

TONE: {tone_instructions.get(tone, tone_instructions['professional'])}

COMPLIANCE REQUIREMENTS:
- Always disclose affiliate relationships clearly
- Make honest, accurate claims backed by evidence
- Avoid exaggerated or misleading statements
- Include appropriate disclaimers
- Follow FTC guidelines for affiliate marketing

QUALITY STANDARDS:
- Write original, unique content
- Provide genuine value to readers
- Use clear, engaging language
- Structure content for readability
- Include relevant examples and details"""
        
        if constraints:
            system_prompt += "\n\nCONSTRAINTS:"
            if constraints.get('word_count'):
                system_prompt += f"\n- Target word count: {constraints['word_count']} words"
            if constraints.get('keywords'):
                system_prompt += f"\n- Include keywords: {', '.join(constraints['keywords'])}"
            if constraints.get('avoid_terms'):
                system_prompt += f"\n- Avoid terms: {', '.join(constraints['avoid_terms'])}"
        
        return system_prompt
    
    def _build_user_prompt(
        self,
        content_type: str,
        structure: List[str],
        product_info: Dict[str, Any],
        marketing_angle: str,
        additional_context: Optional[str],
        constraints: Optional[Dict[str, Any]],
        email_sequence_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the user prompt with product info and structure"""

        # Handle email sequence specially
        if content_type == 'email_sequence' and email_sequence_config:
            return self._build_email_sequence_prompt(
                product_info,
                marketing_angle,
                additional_context,
                constraints,
                email_sequence_config
            )

        user_prompt = f"""Create a {content_type} for the following product using the {marketing_angle} marketing angle.

PRODUCT INFORMATION:
"""

        # Add product details
        if product_info.get('title'):
            user_prompt += f"Product Name: {product_info['title']}\n"

        if product_info.get('description'):
            user_prompt += f"Description: {product_info['description']}\n"

        if product_info.get('price'):
            user_prompt += f"Price: {product_info['price']}\n"

        if product_info.get('features'):
            user_prompt += f"\nKey Features:\n"
            for feature in product_info['features'][:10]:  # Limit to top 10
                user_prompt += f"- {feature}\n"

        if product_info.get('benefits'):
            user_prompt += f"\nKey Benefits:\n"
            for benefit in product_info['benefits'][:10]:
                user_prompt += f"- {benefit}\n"

        if product_info.get('target_audience'):
            user_prompt += f"\nTarget Audience: {product_info['target_audience']}\n"

        if product_info.get('pain_points'):
            user_prompt += f"\nPain Points Addressed:\n"
            for pain_point in product_info['pain_points'][:5]:
                user_prompt += f"- {pain_point}\n"

        # Add additional context from RAG
        if additional_context:
            user_prompt += f"\n\nADDITIONAL CONTEXT:\n{additional_context}\n"

        # Add structure requirements
        user_prompt += f"\n\nCONTENT STRUCTURE:\n"
        user_prompt += "Please organize the content with the following sections:\n"
        for i, section in enumerate(structure, 1):
            section_name = section.replace('_', ' ').title()
            user_prompt += f"{i}. {section_name}\n"

        # Add specific instructions based on content type
        user_prompt += self._get_content_type_instructions(content_type)

        # Add marketing angle guidance
        user_prompt += self._get_marketing_angle_guidance(marketing_angle)

        # Enforce word count for emails
        if content_type == 'email' and constraints and constraints.get('length'):
            length = constraints['length']
            if length == 'short':
                user_prompt += "\n\nCRITICAL: Email must be exactly 50-70 words."
            elif length == 'medium':
                user_prompt += "\n\nCRITICAL: Email must be exactly 100-130 words."
            elif length == 'long':
                user_prompt += "\n\nCRITICAL: Email must be exactly 250-350 words."

        return user_prompt

    def _build_email_sequence_prompt(
        self,
        product_info: Dict[str, Any],
        marketing_angle: str,
        additional_context: Optional[str],
        constraints: Optional[Dict[str, Any]],
        email_sequence_config: Dict[str, Any]
    ) -> str:
        """Build a prompt specifically for email sequences"""

        num_emails = email_sequence_config.get('num_emails', 5)
        sequence_type = email_sequence_config.get('sequence_type', 'cold_to_hot')

        user_prompt = f"""Create an email sequence of {num_emails} emails using the {marketing_angle} marketing angle.
Sequence Type: {sequence_type}

PROGRESSION STRATEGY:
"""

        # Add progression logic based on sequence type
        if sequence_type == 'cold_to_hot':
            user_prompt += """This sequence should guide cold prospects (no prior awareness) to become hot prospects (ready to buy):
- Early emails: Build awareness, establish problem
- Middle emails: Provide value, build trust, introduce solution
- Later emails: Stronger pitch, social proof, urgency, clear CTA

"""
        elif sequence_type == 'warm_to_hot':
            user_prompt += """This sequence should nurture warm prospects (some awareness/interest) to become hot prospects:
- Early emails: Reinforce value, address concerns
- Middle emails: Social proof, differentiation, benefits
- Later emails: Strong offer, urgency, clear CTA

"""
        elif sequence_type == 'hot_close':
            user_prompt += """This sequence should convert hot prospects (already interested) to buyers:
- Early emails: Address final objections
- Middle emails: Social proof, risk reversal, bonuses
- Later emails: Urgent offer, limited time, clear CTA

"""

        user_prompt += "PRODUCT INFORMATION:\n"

        # Add product details
        if product_info.get('title'):
            user_prompt += f"Product Name: {product_info['title']}\n"

        if product_info.get('description'):
            user_prompt += f"Description: {product_info['description']}\n"

        if product_info.get('features'):
            user_prompt += f"\nKey Features:\n"
            for feature in product_info['features'][:10]:
                user_prompt += f"- {feature}\n"

        if product_info.get('benefits'):
            user_prompt += f"\nKey Benefits:\n"
            for benefit in product_info['benefits'][:10]:
                user_prompt += f"- {benefit}\n"

        if product_info.get('target_audience'):
            user_prompt += f"\nTarget Audience: {product_info['target_audience']}\n"

        if product_info.get('pain_points'):
            user_prompt += f"\nPain Points Addressed:\n"
            for pain_point in product_info['pain_points'][:5]:
                user_prompt += f"- {pain_point}\n"

        # Add additional context from RAG
        if additional_context:
            user_prompt += f"\n\nADDITIONAL CONTEXT:\n{additional_context}\n"

        # Get word count target from constraints or use default
        word_count_target = "60-120"
        if constraints and constraints.get('length'):
            length = constraints['length']
            if length == 'short':
                word_count_target = "50-70"
            elif length == 'medium':
                word_count_target = "100-130"
            elif length == 'long':
                word_count_target = "250-350"

        user_prompt += f"""
EMAIL SEQUENCE REQUIREMENTS:
- Generate exactly {num_emails} separate emails
- STRICT WORD COUNT: Each email body must be {word_count_target} words ONLY
- Include a clear, compelling subject line for each email
- Include a clear CTA in each email (adapted to the prospect temperature)
- Maintain consistent tone and voice throughout
- Progress logically from awareness to action
- Include affiliate disclosure where appropriate
- Each email should provide standalone value

CRITICAL: Do not exceed the word count limit. Keep emails concise and to the point.

FORMAT:
For each email, provide:
1. Subject Line: [subject]
2. Email Body: [content - exactly {word_count_target} words]

Separate each email with: === END OF EMAIL {num_emails} ===

Begin the sequence now:"""

        return user_prompt
    
    def _get_content_type_instructions(self, content_type: str) -> str:
        """Get specific instructions for each content type"""
        
        instructions = {
            'review_article': """
REVIEW GUIDELINES:
- Start with a compelling hook that addresses a reader pain point
- Provide an honest, balanced assessment
- Include both strengths and potential limitations
- Use specific examples and scenarios
- End with a clear recommendation
- Include affiliate disclosure at the beginning""",
            
            'comparison': """
COMPARISON GUIDELINES:
- Create a fair, objective comparison
- Use consistent criteria across products
- Highlight unique selling points of each option
- Provide clear winner for different use cases
- Include a comparison table if applicable
- Help readers make the best choice for their needs""",
            
            'tutorial': """
TUTORIAL GUIDELINES:
- Break down complex processes into simple steps
- Use numbered lists for step-by-step instructions
- Include tips and warnings where relevant
- Anticipate common questions and mistakes
- Make it actionable and easy to follow
- End with next steps or advanced tips""",
            
            'landing_page': """
LANDING PAGE GUIDELINES:
- Lead with a powerful, benefit-driven headline
- Focus on transformation and results
- Use bullet points for easy scanning
- Include multiple clear CTAs
- Address objections proactively
- Create urgency without being pushy
- Use social proof strategically""",
            
            'email': """
EMAIL GUIDELINES:
- Keep email body concise and focused (50-150 words)
- Use short paragraphs for easy mobile reading
- Include a clear, compelling subject line
- Have one clear call-to-action
- Include affiliate disclosure where appropriate
- Write in a conversational, friendly tone""",

            'email_sequence': """
EMAIL SEQUENCE GUIDELINES:
- Each email should have one clear purpose
- Build relationship and trust progressively
- Provide value in every email
- Use storytelling to engage
- Include clear, compelling CTAs
- Maintain consistent voice and branding""",
            
            'social_media': """
SOCIAL MEDIA GUIDELINES:
- Start with an attention-grabbing hook
- Keep it concise and scannable
- Use emojis strategically (if appropriate)
- Include a clear call-to-action
- Optimize for platform (character limits, hashtags)
- Make it shareable and engaging""",
            
            'video_script': """
VIDEO SCRIPT GUIDELINES:
- Hook viewers in the first 5 seconds
- Write for spoken delivery (conversational)
- Include visual cues and demonstrations
- Maintain energy and pacing
- Use pattern interrupts to maintain attention
- End with a strong, clear CTA"""
        }
        
        return instructions.get(content_type, "")
    
    def _get_marketing_angle_guidance(self, marketing_angle: str) -> str:
        """Get guidance for specific marketing angles"""
        
        angle_guidance = {
            'Problem-Solution': """
MARKETING ANGLE: Problem-Solution
- Lead with the problem and its impact
- Agitate the pain points
- Present the product as the solution
- Show before/after transformation
- Focus on relief and resolution""",
            
            'Benefit-Driven': """
MARKETING ANGLE: Benefit-Driven
- Focus on outcomes and results
- Emphasize transformation
- Use specific, measurable benefits
- Paint a picture of life after using the product
- Connect benefits to emotional desires""",
            
            'Feature-Rich': """
MARKETING ANGLE: Feature-Rich
- Highlight unique features
- Explain how features translate to benefits
- Compare features to alternatives
- Show technical superiority
- Appeal to detail-oriented buyers""",
            
            'Social Proof': """
MARKETING ANGLE: Social Proof
- Lead with testimonials and success stories
- Use specific numbers and results
- Include diverse user experiences
- Show widespread adoption
- Build trust through others' experiences""",
            
            'Scarcity/Urgency': """
MARKETING ANGLE: Scarcity/Urgency
- Highlight limited availability
- Use time-sensitive offers
- Show what they'll miss out on
- Create FOMO (Fear of Missing Out)
- Be honest and ethical with urgency""",
            
            'Authority/Expert': """
MARKETING ANGLE: Authority/Expert
- Establish credibility
- Reference expert opinions
- Use data and research
- Show industry recognition
- Position as the trusted choice"""
        }
        
        return angle_guidance.get(marketing_angle, f"\nMARKETING ANGLE: {marketing_angle}\n")
    
    def build_refinement_prompt(
        self,
        original_content: str,
        feedback: str,
        content_type: str
    ) -> str:
        """
        Build a prompt for refining existing content
        
        Args:
            original_content: The original generated content
            feedback: User feedback or refinement instructions
            content_type: Type of content
            
        Returns:
            Refinement prompt
        """
        
        prompt = f"""Please refine the following {content_type} based on the feedback provided.

ORIGINAL CONTENT:
{original_content}

FEEDBACK/REFINEMENT INSTRUCTIONS:
{feedback}

Please provide the refined version that addresses the feedback while maintaining the overall structure and quality of the content. Keep all compliance requirements and affiliate disclosures intact."""
        
        return prompt
    
    def build_variation_prompt(
        self,
        base_content: str,
        variation_type: str,
        content_type: str
    ) -> str:
        """
        Build a prompt for creating content variations
        
        Args:
            base_content: Base content to create variations from
            variation_type: Type of variation (tone, angle, length, etc.)
            content_type: Type of content
            
        Returns:
            Variation prompt
        """
        
        variation_instructions = {
            'tone': "Create a variation with a different tone while keeping the same information and structure.",
            'angle': "Create a variation using a different marketing angle while covering the same product.",
            'length': "Create a shorter/longer variation while maintaining key points.",
            'audience': "Create a variation targeted at a different audience segment."
        }
        
        prompt = f"""Based on the following {content_type}, create a variation.

BASE CONTENT:
{base_content}

VARIATION TYPE: {variation_type}
{variation_instructions.get(variation_type, 'Create a unique variation of this content.')}

Maintain compliance requirements and overall quality while creating a fresh take on the content."""
        
        return prompt