"""
Prompt Builder - Constructs optimized prompts for AI content generation
Handles different content types and marketing angles

DEPRECATION NOTICE:
This module is being phased out in favor of PromptGeneratorService.
For new development, use: app/services/prompt_generator_service.py

The PromptGeneratorService provides:
- Unified prompt generation across all content types
- AI-friendly video prompts (no timestamps/production cues)
- Campaign intelligence integration
- Keyword selection API

Migration: Use /api/prompt/generate endpoint instead of direct PromptBuilder usage.
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
                'affiliate_disclosure',
                'problem_agitation',
                'solution_introduction',
                'benefits_list',
                'social_proof',
                'cta_primary',
                'features_section',
                'faq',
                'cta_final',
                'disclaimer_and_disclosures'
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
            'system': """You are an expert AI video prompt writer who creates detailed, flowing narrative descriptions for AI video generation platforms.
Your prompts must be detailed and descriptive (20+ words), covering visual scenes, camera movement, lighting, transitions, and mood.
Write in flowing paragraphs that paint a complete picture for video generation.""",
            'structure': [
                'opening_scene',
                'main_content',
                'closing_scene'
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
        email_sequence_config: Optional[Dict[str, Any]] = None,
        video_config: Optional[Dict[str, Any]] = None
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
            video_config: Video-specific configuration (type, atmosphere, lighting, style, pace, etc.)

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
                constraints,
                content_type=content_type,
                video_config=video_config
            )

            # Build user prompt
            user_prompt = self._build_user_prompt(
                content_type=content_type,
                structure=template['structure'],
                product_info=product_info,
                marketing_angle=marketing_angle,
                additional_context=additional_context,
                constraints=constraints,
                email_sequence_config=email_sequence_config,
                video_config=video_config
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
        constraints: Optional[Dict[str, Any]],
        content_type: Optional[str] = None,
        video_config: Optional[Dict[str, Any]] = None
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
- Follow FTC guidelines for affiliate marketing"""

        # Add email-specific compliance requirements
        if content_type == 'email_sequence':
            system_prompt += """
- 🚨 CRITICAL FOR EMAIL SEQUENCES: EVERY email must include affiliate disclosure and unsubscribe link
- This is required by FTC regulations and CAN-SPAM Act - no exceptions
- Emails without proper disclosure and unsubscribe will be rejected"""

        system_prompt += """

QUALITY STANDARDS:
- Write original, unique content
- Provide genuine value to readers
- Use clear, engaging language
- Structure content for readability
- Include relevant examples and details"""

        if constraints:
            system_prompt += "\n\nCONSTRAINTS:"
            if constraints.get('word_count'):
                system_prompt += f"\n- IMPORTANT: Keep content to EXACTLY {constraints['word_count']} words (±10%). Count your words carefully."
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
        email_sequence_config: Optional[Dict[str, Any]] = None,
        video_config: Optional[Dict[str, Any]] = None
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
            user_prompt += f"\n\nADDITIONAL CONTEXT (CAMPAIGN INTELLIGENCE):\n{additional_context}\n"
            user_prompt += f"\n[IMPORTANT] Use this intelligence data to create your video script!\n"

        # Add video-specific configuration
        if content_type == 'video_script' and video_config:
            user_prompt += f"\n\n🎬 AI VIDEO PROMPT REQUIREMENTS:\n"
            user_prompt += "=" * 60 + "\n\n"

            # Get duration from video_format (now using seconds like "5s", "10s", "15s", "20s")
            video_format = video_config.get('video_format', '10s')
            if hasattr(video_format, 'value'):
                format_str = video_format.value
            else:
                format_str = str(video_format)

            # Extract duration in seconds
            duration_seconds = 10  # default
            if 's' in format_str:
                try:
                    duration_seconds = int(format_str.replace('s', ''))
                except:
                    duration_seconds = 10

            user_prompt += f"Video Duration: {duration_seconds} seconds\n"
            if video_config.get('video_type'):
                user_prompt += f"Video Type: {video_config['video_type'].replace('_', ' ').title()}\n"

            # Skip video format sections for video_script - handled separately below
            if content_type != 'video_script':
                user_prompt += "\n[AI VIDEO PROMPT FORMAT]\n"
                user_prompt += "- Write a SINGLE flowing narrative description\n"
                user_prompt += "- NO timestamps like [0-3s] or [5-10s]\n"
                user_prompt += "- NO production cues like [VISUAL:], [B-ROLL:], [ANGLE:]\n"
                user_prompt += "- Describe scenes visually in present tense\n"
                user_prompt += "- Keep total prompt under 200 words\n\n"

                user_prompt += "[SCENE STRUCTURE FOR " + str(duration_seconds) + " SECOND VIDEO]\n"
                user_prompt += "1. OPENING (hook the viewer immediately)\n"
                user_prompt += "2. MAIN CONTENT (show product/benefit visually)\n"
                user_prompt += "3. CLOSING (implied call-to-action)\n\n"

                user_prompt += "[USE INTELLIGENCE DATA]\n"
                user_prompt += "- Reference the product name and key benefits from intelligence\n"
                user_prompt += "- Describe the transformation or problem being solved\n"
                user_prompt += "- Include mood/atmosphere that matches the product\n\n"

        # Add specific instructions based on content type
        if content_type == 'video_script':
            # Extract word_count from constraints
            word_count = constraints.get('word_count') if constraints else None

            # Simplified, direct video script prompt
            user_prompt += f"\n\nWRITE AN AI VIDEO PROMPT:\n"
            user_prompt += f"Create a flowing narrative description for a {int(word_count / 1.75) if word_count else 10}-second video.\n"
            user_prompt += f"Write in present tense, describing visual scenes and transitions.\n"
            user_prompt += f"Include: camera movement, lighting, mood, and atmosphere.\n"
            user_prompt += f"Target: {word_count if word_count else 25} words of detailed description.\n"
            user_prompt += f"Format: Single flowing paragraph (NO bullet points, NO timestamps).\n"
        else:
            # Add structure requirements for non-video content
            user_prompt += f"\n\nCONTENT STRUCTURE:\n"
            user_prompt += "Please organize the content with the following sections:\n"
            for i, section in enumerate(structure, 1):
                section_name = section.replace('_', ' ').title()
                user_prompt += f"{i}. {section_name}\n"

            # Add specific instructions for non-video content
            user_prompt += self._get_content_type_instructions(content_type)
            user_prompt += self._get_marketing_angle_guidance(marketing_angle)

            # Enforce word count for non-video content
            if constraints and constraints.get('word_count'):
                word_count = constraints['word_count']
                user_prompt += f"\n\n⚠️ CRITICAL WORD COUNT REQUIREMENT ⚠️"
                user_prompt += f"\nYour response MUST be approximately {word_count} words (±10% is acceptable)."
                user_prompt += f"\nTarget range: {int(word_count * 0.9)}-{int(word_count * 1.1)} words."
                user_prompt += f"\nCount carefully and adjust before submitting."

        # Final formatting reminder for video scripts
        if content_type == 'video_script':
            user_prompt += f"\n\nWrite a detailed, descriptive paragraph now.\n"

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
        if constraints and constraints.get('word_count'):
            word_count_per_email = constraints['word_count']
            word_count_min = int(word_count_per_email * 0.9)
            word_count_max = int(word_count_per_email * 1.1)
            word_count_target = f"{word_count_min}-{word_count_max}"
        else:
            word_count_per_email = 100
            word_count_target = "90-110"

        user_prompt += f"""
EMAIL SEQUENCE REQUIREMENTS:
- Generate exactly {num_emails} separate emails
- ⚠️ CRITICAL WORD COUNT PER EMAIL ⚠️: Each individual email body must be approximately {word_count_per_email} words ({word_count_target} words acceptable range)
- THIS IS {word_count_per_email} WORDS PER EMAIL, NOT {word_count_per_email} WORDS TOTAL
- Total word count across all {num_emails} emails will be approximately {word_count_per_email * num_emails} words
- Include a clear, compelling subject line for each email
- Include a clear CTA in each email (adapted to the prospect temperature)
- Maintain consistent tone and voice throughout
- Progress logically from awareness to action
- Each email should provide standalone value

🚨 MANDATORY LEGAL FOOTER - MUST APPEAR IN EVERY EMAIL 🚨
Copy this EXACT footer to the bottom of EVERY SINGLE email (all {num_emails} emails):

---
Affiliate Disclosure: This email contains affiliate links. I may earn a commission from purchases made through these links.
Unsubscribe: Click here to unsubscribe from future emails.
---

DO NOT SKIP THIS FOOTER. It is required by FTC regulations and CAN-SPAM Act.
Every email that does not include this footer will FAIL compliance and be rejected.

⚠️ CRITICAL: Each email must be {word_count_per_email} words (±10%). Count carefully for EACH email separately.

FORMAT EXAMPLE:
Subject Line: [Your compelling subject]

[Email content - approximately {word_count_per_email} words]

[Your email message and CTA here...]

---
Affiliate Disclosure: This email contains affiliate links. I may earn a commission from purchases made through these links.
Unsubscribe: Click here to unsubscribe from future emails.
---

=== END OF EMAIL 1 ===

IMPORTANT: ALL {num_emails} EMAILS MUST INCLUDE THE FOOTER SHOWN ABOVE.

Begin generating the {num_emails}-email sequence now:"""

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
- Include a clear, prominent **Affiliate Disclosure** section right after the subheadline
- The disclosure should state: "This page contains affiliate links. We may earn a commission if you make a purchase through these links at no additional cost to you."
- Focus on transformation and results
- Use bullet points for easy scanning
- Include multiple clear CTAs with tracked links - use phrases like "click here to learn more", "visit the website", or "check it out" (these will automatically become clickable tracked links)
- Address objections proactively
- Create urgency without being pushy
- Use social proof strategically
- End with a **Disclaimer and Disclosures** section that includes FTC disclaimers, results disclaimers, and CAN-SPAM compliance info""",
            
            'email': """
EMAIL GUIDELINES:
- Keep email body concise and focused (50-150 words)
- Use short paragraphs for easy mobile reading
- Include a clear, compelling subject line
- Have one clear call-to-action - use phrases like "click here to learn more" or "check it out" (these will automatically become clickable tracked links)
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
AI VIDEO PROMPT GUIDELINES:

FORMAT:
- Write a single flowing narrative description (NOT a production script)
- NO timestamps like [0-3s] or [5-10s]
- NO production cues like [VISUAL:], [B-ROLL:], [ANGLE:], [LIGHTING:]
- NO bullet points or numbered lists
- Write in present tense, describing what happens visually

STRUCTURE (describe in flowing prose):
1. OPENING - Eye-catching opening scene that hooks the viewer
2. MAIN CONTENT - Visual storytelling showing the product/message
3. CLOSING - Strong ending with implied call-to-action

WRITING STYLE:
- Describe scenes visually: "A woman smiles confidently in morning light..."
- Include motion and transitions: "Camera slowly zooms in...", "Scene transitions to..."
- Mention mood and atmosphere: "warm, inviting atmosphere", "professional studio setting"
- Be specific about subjects: people, products, environments
- Keep prompt concise but detailed enough for video generation
- Focus on transformation and benefits

PROHIBITED:
- NO timestamps or time markers
- NO [BRACKETS] for production notes
- NO numbered shot lists
- NO "Narrator:" or "VO:" prefixes
- NO landing page style content"""
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