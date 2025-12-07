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
            'system': """You are an expert video script writer who creates professional, production-ready video scripts.
Your scripts are formatted for video production with timestamps, visual cues, and cinematic elements.
You understand pacing, visual storytelling, and platform-specific optimization.""",
            'structure': [
                'hook',
                'disclosure',
                'problem',
                'solution',
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
            user_prompt += f"\n\n🎬 VIDEO PRODUCTION REQUIREMENTS:\n"
            user_prompt += "=" * 60 + "\n\n"

            if video_config.get('video_type'):
                user_prompt += f"Video Type: {video_config['video_type'].replace('_', ' ').title()}\n"
            if video_config.get('video_format'):
                user_prompt += f"Video Format: {video_config['video_format'].replace('_', ' ').title()}\n"

            user_prompt += "\n"

            # Format-specific guidance
            video_format = video_config.get('video_format', 'long_form')
            user_prompt += "\n[FORMAT REQUIREMENTS]\n"
            if video_format == 'short_form':
                user_prompt += "- Duration: 15-20 seconds MAX\n- Structure: Hook (0-3s) → Disclosure (3-5s) → Problem (5-8s) → Solution/Demo (8-15s) → CTA (15-20s)\n- Every second counts - no filler\n- Visual should support every word\n"
            elif video_format == 'long_form':
                user_prompt += "- Duration: 1-5 minutes\n- Can include storytelling elements\n- More detailed demonstration\n- Build trust and authority\n"
            elif video_format == 'story':
                user_prompt += "- Duration: 15 seconds exactly\n- Hook → Quick showcase → CTA\n- Ultra-focused message\n"

            user_prompt += "\n[PRODUCTION ELEMENTS]\n"
            if video_config.get('include_camera_angles'):
                user_prompt += "✓ Include camera angle notes: [ANGLE: close-up/wide/POV/drone/over-shoulder]\n"
            if video_config.get('include_visual_cues'):
                user_prompt += "✓ Include visual cues: [VISUAL: scene description] or [B-ROLL: footage needed]\n"
            if video_config.get('include_transitions'):
                user_prompt += "✓ Include transitions: [TRANSITION: cut/fade/zoom/slide]\n"

            user_prompt += "\n[CRITICAL FORMATTING]\n"
            user_prompt += "- MUST start each line with [TIMESTAMP]\n"
            user_prompt += "- Example: [0-3s] Your spoken content here\n"
            user_prompt += "- Include production notes in brackets: [VISUAL:], [ANGLE:], [LIGHTING:], [TRANSITION:]\n"
            user_prompt += "- NO landing page formatting (no **bold headers**, no paragraph blocks)\n"
            user_prompt += "- YES to screenplay format with timing and visuals\n\n"

            user_prompt += "[USE INTELLIGENCE DATA - MANDATORY]\n"
            user_prompt += "✅ Reference the CAMPAIGN INTELLIGENCE provided above in EVERY section:\n"
            user_prompt += "  - Hook: Use problem/pain point from intelligence\n"
            user_prompt += "  - Problem: Emphasize the pain points from intelligence data\n"
            user_prompt += "  - Solution: Highlight BENEFITS and KEY FEATURES from intelligence\n"
            user_prompt += "  - Demo: Show how product solves the problem (use key points)\n"
            user_prompt += "  - CTA: Mention specific benefit or result from intelligence\n"
            user_prompt += "✅ DO NOT make up benefits - use only what's in the intelligence\n"
            user_prompt += "✅ Use exact phrases from intelligence data where possible\n\n"

        # Add structure requirements
        user_prompt += f"\n\nCONTENT STRUCTURE:\n"
        if content_type == 'video_script':
            user_prompt += "VIDEO SCRIPT FORMAT (MUST FOLLOW EXACTLY):\n"
            user_prompt += "Each line MUST start with [TIMESTAMP] followed by content.\n"
            user_prompt += "Include production notes in [BRACKETS] after the spoken words.\n\n"
            for i, section in enumerate(structure, 1):
                section_name = section.replace('_', ' ').title()
                user_prompt += f"{i}. {section_name} (include [TIMESTAMP])\n"
            user_prompt += "\nExample format:\n"
            user_prompt += "[0-3s] Are you tired of struggling with stubborn belly fat?\n"
            user_prompt += "[VISUAL: Close-up on speaker, direct eye contact]\n"
            user_prompt += "[ANGLE: Medium shot]\n"
            user_prompt += "[LIGHTING: Bright, professional setup]\n"
            user_prompt += "\n"
            user_prompt += "[3-5s] This video contains affiliate links. I may earn a commission if you purchase through my link at no extra cost to you.\n"
            user_prompt += "[VISUAL: Text overlay on screen - 'This video contains affiliate links']\n"
            user_prompt += "[TRANSITION: Quick fade in]\n"
            user_prompt += "\n"
            user_prompt += "[5-8s] I tried everything - diets, workouts, supplements - nothing worked until I discovered AquaSculpt.\n"
            user_prompt += "[B-ROLL: Frustrated person looking in mirror]\n\n"
        else:
            user_prompt += "Please organize the content with the following sections:\n"
            for i, section in enumerate(structure, 1):
                section_name = section.replace('_', ' ').title()
                user_prompt += f"{i}. {section_name}\n"

        # Add specific instructions based on content type
        user_prompt += self._get_content_type_instructions(content_type)

        # Add marketing angle guidance
        user_prompt += self._get_marketing_angle_guidance(marketing_angle)

        # Enforce word count or duration constraint
        if constraints and constraints.get('word_count'):
            word_count = constraints['word_count']

            if content_type == 'video_script':
                # Calculate original spoken words from total (we overestimated by 75%)
                spoken_words = int(word_count / 1.75)  # Reverse the 75% production estimate
                user_prompt += f"\n\n🎬 VIDEO DURATION GUIDANCE"
                user_prompt += f"\nTarget spoken words: ~{spoken_words} words (average 2.5 words/second)"
                user_prompt += f"\nEstimated speaking time: {int(spoken_words / 2.5)} seconds"
                user_prompt += f"\nTotal word budget (including production notes): {word_count} words"
                user_prompt += f"\nIMPORTANT: {spoken_words} words refers to SPOKEN content only"
                user_prompt += f"\nProduction notes ([VISUAL:], [ANGLE:], etc.) use the remaining {word_count - spoken_words} words"
                user_prompt += f"\n\n⚠️ CRITICAL: Complete ALL 5 sections (Hook, Disclosure, Problem, Solution, CTA)"
                user_prompt += f"\nDo NOT stop early - finish every section with full production notes"
            else:
                user_prompt += f"\n\n⚠️ CRITICAL WORD COUNT REQUIREMENT ⚠️"
                user_prompt += f"\nYour response MUST be approximately {word_count} words (±10% is acceptable)."
                user_prompt += f"\nTarget range: {int(word_count * 0.9)}-{int(word_count * 1.1)} words."
                user_prompt += f"\nCount carefully and adjust before submitting."

        # Final formatting reminder for video scripts
        if content_type == 'video_script':
            # Determine video format and set appropriate timestamps
            video_format = video_config.get('video_format', 'short_form') if video_config else 'short_form'
            # Handle both enum objects and string values
            if hasattr(video_format, 'value'):
                format_str = video_format.value
            else:
                format_str = str(video_format)
            # Normalize to lowercase for comparison
            format_str = format_str.lower().replace('videoformat.', '')
            logger.info(f"[PromptBuilder] video_format raw={video_format}, format_str={format_str}")

            # Set timestamps based on video format (format_str is already normalized to lowercase)
            if format_str == 'long_form':
                # Long-form video (1+ minute = 60-90 seconds)
                timestamp_ranges = {
                    'hook': '[0-10s]',
                    'disclosure': '[10-15s]',
                    'problem': '[15-30s]',
                    'solution': '[30-50s]',
                    'benefits': '[50-70s]',
                    'social_proof': '[70-80s]',
                    'cta': '[80-90s]'
                }
                user_prompt += f"\n\n🎬 VIDEO FORMAT: LONG-FORM (60-90 seconds)"
                user_prompt += f"\n⚠️ CRITICAL: This is a LONG-FORM video. Your script MUST include timestamps up to 80-90 seconds."
                user_prompt += f"\nTimestamp structure: {timestamp_ranges}"
                user_prompt += f"\nYou MUST generate content for ALL timestamps: [0-10s], [10-15s], [15-30s], [30-50s], [50-70s], [70-80s], [80-90s]"
                logger.info(f"[PromptBuilder] Long-form video detected, using timestamps: {timestamp_ranges}")
            elif format_str == 'story':
                # Story format (15 seconds)
                timestamp_ranges = {
                    'hook': '[0-3s]',
                    'disclosure': '[3-5s]',
                    'problem': '[5-8s]',
                    'solution': '[8-12s]',
                    'cta': '[12-15s]'
                }
                user_prompt += f"\n\n🎬 VIDEO FORMAT: STORY (15 seconds) - Using timestamps: {timestamp_ranges}"
                logger.info(f"[PromptBuilder] Story format video detected, using timestamps: {timestamp_ranges}")
            else:
                # Default: Short-form video (15-20 seconds)
                timestamp_ranges = {
                    'hook': '[0-3s]',
                    'disclosure': '[3-5s]',
                    'problem': '[5-8s]',
                    'solution': '[8-15s]',
                    'cta': '[15-18s]'
                }
                user_prompt += f"\n\n🎬 VIDEO FORMAT: SHORT-FORM (15-20 seconds) - Using timestamps: {timestamp_ranges}"
                logger.info(f"[PromptBuilder] Short-form video detected, using timestamps: {timestamp_ranges}")

            user_prompt += f"\n\n" + "=" * 60
            user_prompt += f"\n🎬 FINAL CHECKLIST - Your script MUST include:"
            user_prompt += f"\n✓ [TIMESTAMP] at the start of EVERY line"
            user_prompt += f"\n✓ [VISUAL:] cues for what to show"
            user_prompt += f"\n✓ [ANGLE:] camera direction (if enabled)"
            user_prompt += f"\n✓ [LIGHTING:] style notes (if required)"
            user_prompt += f"\n✓ EXACT disclosure text in {timestamp_ranges['disclosure']} section:"
            user_prompt += f"\n  'This video contains affiliate links. I may earn a commission"
            user_prompt += f"\n  if you purchase through my link at no extra cost to you.'"
            user_prompt += f"\n✓ [VISUAL: Text overlay on screen] AFTER disclosure"
            user_prompt += f"\n✓ Hook in {timestamp_ranges['hook']} BEFORE disclosure"
            user_prompt += f"\n✓ Problem in {timestamp_ranges['problem']} AFTER disclosure"
            user_prompt += f"\n✓ Solution/Demo in {timestamp_ranges['solution']}"

            # Add additional sections for long-form videos
            if format_str == 'long_form':
                user_prompt += f"\n✓ Benefits showcase in {timestamp_ranges.get('benefits', '[50-70s]')}"
                user_prompt += f"\n✓ Social proof/testimonials in {timestamp_ranges.get('social_proof', '[70-80s]')}"

            user_prompt += f"\n✓ CTA in {timestamp_ranges['cta']} with urgency"
            user_prompt += f"\n✓ Use campaign intelligence data from above"
            user_prompt += f"\n✓ NO landing page formatting (**headlines**, paragraphs)"
            user_prompt += f"\n✓ YES to screenplay format (timestamps + visuals)"
            user_prompt += f"\n"
            user_prompt += f"\n" + "=" * 60
            user_prompt += f"\n⚠️ CRITICAL COMPLETION REQUIREMENT ⚠️"

            if format_str == 'long_form':
                user_prompt += f"\nYou MUST complete ALL 7 sections for LONG-FORM video:"
                user_prompt += f"\n1. Hook {timestamp_ranges['hook']}"
                user_prompt += f"\n2. Disclosure {timestamp_ranges['disclosure']}"
                user_prompt += f"\n3. Problem {timestamp_ranges['problem']}"
                user_prompt += f"\n4. Solution/Demo {timestamp_ranges['solution']}"
                user_prompt += f"\n5. Benefits {timestamp_ranges.get('benefits', '[50-70s]')}"
                user_prompt += f"\n6. Social Proof {timestamp_ranges.get('social_proof', '[70-80s]')}"
                user_prompt += f"\n7. CTA {timestamp_ranges['cta']}"
                user_prompt += f"\n\n⚠️ DO NOT STOP AT 15-20 SECONDS. This is a 60-90 second video!"
            else:
                user_prompt += f"\nYou MUST complete ALL sections listed above (Hook, Disclosure, Problem, Solution/Demo, CTA)."

            user_prompt += f"\nDO NOT stop mid-generation. Every section must be fully written out with timestamps."
            user_prompt += f"\nYour response will be cut off if incomplete, so finish all sections completely."
            user_prompt += f"\nEND YOUR RESPONSE ONLY AFTER completing the final CTA section."
            user_prompt += f"\n"
            user_prompt += f"\nIMPORTANT: The word limit is for SPOKEN content only."
            user_prompt += f"\nYou MUST include production notes ([VISUAL:], [ANGLE:], etc.) even if it exceeds the word count."
            user_prompt += f"\nThe word count is a GUIDELINE, not a hard stop. Completeness is more important."
            user_prompt += f"\n" + "=" * 60 + "\n"

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
VIDEO SCRIPT GUIDELINES:

FORMATTING (MANDATORY):
- EVERY line must start with [TIMESTAMP] (e.g., [0-3s], [3-5s], [5-8s])
- NO other text before the timestamp
- NO double brackets [[ ]]
- Include production notes in separate lines: [VISUAL:], [ANGLE:], [LIGHTING:], [TRANSITION:]

DISCLOSURE (CRITICAL - MUST FOLLOW EXACTLY):
- MUST be its own timestamp segment
- MUST use this EXACT wording: "This video contains affiliate links. I may earn a commission if you purchase through my link at no extra cost to you."
- MUST include: [VISUAL: Text overlay on screen] after the disclosure

REQUIRED STRUCTURE (MUST INCLUDE ALL 5 SECTIONS):
1. HOOK - Attention-grabbing statement/question
2. DISCLOSURE - Required affiliate disclosure (see above)
3. PROBLEM - Identify the pain point
4. SOLUTION/DEMO - Show the product solution
5. CTA - Clear call-to-action

NOTE: Actual timestamp ranges will be provided in the final checklist based on video format (short-form, long-form, or story).

VISUAL PRODUCTION:
- [VISUAL: detailed scene description] for what to show on screen
- [B-ROLL: specific footage needed]
- [ANGLE: close-up/wide/medium/POV/over-shoulder/drone]
- [LIGHTING: bright/soft/warm/cool/dramatic/natural/cinematic]
- [TRANSITION: cut/fade/zoom/slide/dissolve]

WRITING STYLE:
- Conversational, speak directly to one person
- Keep sentences short and punchy
- Use "you" and "your" to engage viewer
- Avoid jargon or complex words

CTA REQUIREMENTS:
- Clear action (link in bio, tap link, visit website)
- Include urgency or scarcity
- Mention specific benefit

PROHIBITED:
- NO **bold headers**
- NO paragraph blocks
- NO "Headline:" or "Subheadline:" format
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