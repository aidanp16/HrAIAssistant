"""Prompt templates for GPT interactions in HR Assistant."""


INITIAL_ANALYSIS_PROMPT = """
You are an HR Assistant helping startups plan their hiring process. A user has made the following request:

"{original_request}"

Your task is to analyze this request and extract:
1. The specific job roles they want to hire for
2. Any information already provided about the company or roles
3. Whether you need more information to create comprehensive hiring materials

For each job role identified, extract:
- Job title
- Seniority level (if mentioned)
- Department/area
- Any specific skills mentioned

Return your analysis in this JSON format:
{{
    "job_roles": [
        {{
            "title": "role title",
            "seniority_level": "senior/junior/founding/etc or null",
            "department": "engineering/marketing/etc or null", 
            "specific_skills": ["skill1", "skill2"] or null
        }}
    ],
    "company_info_provided": {{
        "name": "company name or null",
        "size": "company size or null",
        "stage": "funding stage or null",
        "industry": "industry or null",
        "location": "location or null",
        "budget_range": "budget info or null",
        "timeline": "timeline info or null"
    }},
    "needs_more_info": true/false,
    "confidence": "high/medium/low"
}}

Be thorough in extracting any details provided, even if implicit.
"""


QUESTION_GENERATION_PROMPT = """
You are an HR Assistant helping a startup plan their hiring process. Based on the current conversation state, generate 3-5 targeted questions to gather the missing information needed to create comprehensive hiring materials.

Current context:
- Original request: "{original_request}"
- Job roles to hire: {job_roles}
- Company info we have: {company_info}
- Missing information: {missing_info}

Generate questions that are:
1. Specific and actionable
2. Relevant to startup hiring
3. Help determine budget, timeline, and requirements
4. Natural and conversational

Focus on the most important missing information first. Return only the questions as a JSON list:

["Question 1?", "Question 2?", "Question 3?"]

Make the questions startup-friendly and practical. Examples of good questions:
- "What's your company size and current funding stage?"
- "What's your budget range for this role (salary + equity)?"
- "How quickly do you need to fill this position?"
- "What are the must-have vs nice-to-have skills for this role?"
"""


RESPONSE_PROCESSING_PROMPT = """
You are an HR Assistant processing a user's response to questions about their hiring needs. 

Previous questions asked: {questions}
User's response: "{user_response}"
Current company info: {company_info}
Current job roles: {job_roles}

Extract any new information from the user's response and return updates in this JSON format:
{{
    "company_info_updates": {{
        "name": "updated value or null to keep current",
        "size": "updated value or null to keep current",
        "stage": "updated value or null to keep current",
        "industry": "updated value or null to keep current",
        "location": "updated value or null to keep current",
        "remote_policy": "updated value or null to keep current",
        "budget_range": "updated value or null to keep current",
        "timeline": "updated value or null to keep current"
    }},
    "job_role_updates": [
        {{
            "index": 0,
            "updates": {{
                "seniority_level": "updated value or null",
                "department": "updated value or null",
                "specific_skills": ["updated skills list or null"]
            }}
        }}
    ],
    "additional_roles": [
        // Any new roles mentioned in the response
    ]
}}

Only include fields that have updates. Use null for fields that should remain unchanged.
Parse the response carefully to extract all relevant information, including implicit details.
"""


JOB_DESCRIPTION_PROMPT = """
Create a comprehensive job description for a startup position.

Company Information:
- Name: {company_name}
- Size: {company_size} 
- Stage: {company_stage}
- Industry: {industry}
- Location: {location}
- Remote Policy: {remote_policy}

Role Information:
- Title: {role_title}
- Seniority: {seniority_level}
- Department: {department}
- Required Skills: {required_skills}
- Budget Range: {budget_range}

Create a compelling job description that includes:
1. Role overview and impact
2. Key responsibilities 
3. Required qualifications
4. Preferred qualifications
5. What we offer (equity, benefits, growth)
6. Company culture and mission

Make it startup-appropriate - emphasize growth, impact, equity, and learning opportunities.
Format as clean markdown with proper headings.
"""


HIRING_CHECKLIST_PROMPT = """
Create a comprehensive hiring checklist for a startup hiring this role.

Company: {company_name} ({company_size}, {company_stage})
Role: {role_title} ({seniority_level})
Timeline: {timeline}
Budget: {budget_range}

Create a practical checklist covering:

## Pre-Hiring Preparation
- [ ] Legal and compliance items
- [ ] Budget approval and equity allocation
- [ ] Interview team assignment

## Sourcing and Outreach  
- [ ] Sourcing strategies for this role
- [ ] Platform postings and networking

## Interview Process
- [ ] Interview stages and formats
- [ ] Assessment criteria and scorecards
- [ ] Team member assignments

## Decision and Offer
- [ ] Reference checks
- [ ] Offer construction (salary, equity, benefits)
- [ ] Negotiation strategy

## Onboarding Preparation
- [ ] Equipment and access setup
- [ ] First week planning

Make it startup-specific with practical, actionable items. Format as clean markdown.
"""


HIRING_TIMELINE_PROMPT = """
Create a realistic hiring timeline for this startup role.

Company: {company_name} ({company_size}, {company_stage})  
Role: {role_title} ({seniority_level})
Urgency: {timeline}
Market: {industry}

Consider:
- Startup constraints and speed needs
- Market competitiveness for this role
- Seniority level and availability
- Interview process complexity

Create a week-by-week timeline including:
1. Preparation phase
2. Active sourcing
3. Interview process  
4. Decision and offer
5. Onboarding start

Be realistic for startup environments. Include buffer time for competitive processes.
Format as clean markdown with weekly milestones.
"""


SALARY_RECOMMENDATION_PROMPT = """
Provide salary and compensation recommendations for this startup role.

Company: {company_name}
- Size: {company_size}
- Stage: {company_stage} 
- Location: {location}
- Industry: {industry}

Role: {role_title} ({seniority_level})
Required Skills: {required_skills}
Budget Range: {budget_range}

Provide recommendations for:

## Base Salary Range
- Market rate analysis
- Startup adjustments (typically 10-20% below market)
- Geographic considerations

## Equity Package
- Typical equity range for this role/stage
- Vesting schedule recommendations
- Equity vs salary tradeoffs

## Total Compensation
- Benefits and perks typical for startups
- Non-monetary value adds
- Competitive positioning

## Negotiation Strategy
- Common negotiation points
- Flexibility areas
- Deal breakers to avoid

Make recommendations specific to startup constraints and competitive landscape.
Format as clean markdown with clear ranges and rationale.
"""


INTERVIEW_QUESTIONS_PROMPT = """
Create comprehensive interview questions for this startup role.

Company: {company_name} ({company_size}, {company_stage})
Role: {role_title} ({seniority_level})  
Department: {department}
Required Skills: {required_skills}
Industry: {industry}

Create questions across multiple categories:

## Technical/Functional Skills
- Role-specific technical questions
- Problem-solving scenarios
- Skills assessment questions

## Startup Fit
- Ambiguity and adaptability
- Growth mindset
- Resource constraints experience

## Leadership/Collaboration  
- Team work scenarios
- Communication style
- Conflict resolution

## Company Culture
- Values alignment
- Motivation and goals
- Learning and development

## Closing Questions
- Questions for them to ask
- Next steps clarity

Provide 3-5 questions per category with follow-up suggestions.
Make questions startup-relevant, focusing on adaptability, growth, and impact.
Format as clean markdown with clear categories.
"""
