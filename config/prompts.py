"""Prompt templates for GPT interactions in HR Assistant."""


INITIAL_ANALYSIS_PROMPT = """
You are an HR Assistant helping startups plan their hiring process. A user has made the following request:

"{original_request}"

IMPORTANT: The company profile (name, size, stage, industry, location, remote policy, description, values, mission) is already stored and complete. You don't need to ask about basic company information.

Your task is to analyze this request and extract:
1. The specific job roles they want to hire for
2. Any role-specific information already provided (skills, timeline, budget)
3. Whether you need more role-specific information to create comprehensive hiring materials

For each job role identified, extract:
- Job title
- Seniority level (if mentioned)
- Department/area
- Any specific skills mentioned

IMPORTANT: Return ONLY valid JSON in the exact format below. No additional text, no markdown formatting, no code blocks.

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
        "location": "location or null"
    }},
    "needs_more_info": true,
    "confidence": "high"
}}

EXAMPLE for "I need to hire a founding engineer and a GenAI intern":
{{
    "job_roles": [
        {{
            "title": "Founding Engineer",
            "seniority_level": "founding",
            "department": "engineering", 
            "specific_skills": null
        }},
        {{
            "title": "GenAI Intern",
            "seniority_level": "intern",
            "department": "engineering", 
            "specific_skills": ["AI", "Machine Learning", "Python"]
        }}
    ],
    "company_info_provided": {{
        "name": null,
        "size": null,
        "stage": null,
        "industry": null,
        "location": null
    }},
    "needs_more_info": true,
    "confidence": "high"
}}
"""


QUESTION_GENERATION_PROMPT = """
You are an HR Assistant helping a startup plan their hiring process. Based on the current conversation state, generate 3 targeted questions to gather the missing information needed to create comprehensive hiring materials.

Current context:
- Original request: "{original_request}"
- Current role focus: {current_role}
- Company info we have: {company_info}
- Missing information for this role: {missing_info}

IMPORTANT: The company profile (name, size, stage, industry, location, remote policy, description, values, mission) is already stored and complete. DO NOT ask questions about basic company information.

IMPORTANT: Focus ONLY on the current role: {current_role_title}. Do not ask about other roles.

Generate questions that are:
1. Specific to this role's requirements (budget, timeline, skills)
2. Relevant to startup hiring
3. Help determine role-specific details for {current_role_title}
4. Natural and conversational
5. Limited to exactly 3 questions

Focus ONLY on missing information for {current_role_title}:
- Budget range for this specific role
- Timeline for filling this position
- Specific skill requirements
- Seniority level preferences

IMPORTANT: Return ONLY a valid JSON array of exactly 3 questions. No additional text, no markdown formatting, no code blocks.

["Question 1?", "Question 2?", "Question 3?"]

EXAMPLE OUTPUT for a founding engineer role:
["What's your budget range for the founding engineer position?", "How quickly do you need to fill the founding engineer role?", "What are the must-have technical skills for the founding engineer?"]

Examples of good role-specific questions:
- "What's your budget range for the [role title] position?"
- "How quickly do you need to fill the [role title] role?"
- "What are the must-have technical skills for the [role title]?"
- "What level of experience do you need for the [role title]?"
- "What's the ideal timeline for onboarding the [role title]?"
"""


RESPONSE_PROCESSING_PROMPT = """
You are an HR Assistant processing a user's response to hiring questions. 

Previous questions: {questions}
User's response: "{user_response}"
Current company info: {company_info}
Current job roles: {job_roles}

Analyze the user's response and extract ANY new information they provided. Return ONLY valid JSON in this exact format:

{{
    "company_info_updates": {{
        "size": null,
        "stage": null,
        "industry": null,
        "location": null,
        "remote_policy": null
    }},
    "job_role_updates": [
        {{
            "index": 0,
            "updates": {{
                "budget_range": null,
                "timeline": null,
                "specific_skills": null,
                "seniority_level": null
            }}
        }}
    ],
    "additional_roles": []
}}

IMPORTANT RULES:
1. Replace null with actual values ONLY if the user provided that information
2. Keep null for any field the user didn't mention
3. Budget and timeline are now ROLE-SPECIFIC, not company-wide
4. If user mentions budget/timeline for specific roles, put in job_role_updates with correct index
5. If user mentions budget/timeline without specifying roles, apply to all roles (create updates for each index)
6. For budget_range, capture salary ranges like "120k-150k" or "$80k-120k"
7. For timeline, capture urgency like "6-8 weeks" or "ASAP" or "2 months"
8. For size, use formats like "100 employees" or "50-person team"
9. For stage, capture funding like "Series B" or "Seed stage"
10. Return ONLY the JSON, no other text
11. Do not include comments in the JSON

Example response for "We're a 100 employee Series B company, budget is 120k-150k for founding engineer, 70k-90k for intern, need to fill both in 6-8 weeks":
{{
    "company_info_updates": {{
        "size": "100 employees",
        "stage": "Series B",
        "industry": null,
        "location": null,
        "remote_policy": null
    }},
    "job_role_updates": [
        {{
            "index": 0,
            "updates": {{
                "budget_range": "$120k-150k",
                "timeline": "6-8 weeks",
                "specific_skills": null,
                "seniority_level": null
            }}
        }},
        {{
            "index": 1,
            "updates": {{
                "budget_range": "$70k-90k",
                "timeline": "6-8 weeks",
                "specific_skills": null,
                "seniority_level": null
            }}
        }}
    ],
    "additional_roles": []
}}
"""


JOB_DESCRIPTION_PROMPT = """
Create a comprehensive job description for a startup position.

Company Information:
- Name: {company_name}
- Description: {company_description}
- Values: {company_values}
- Mission: {company_mission}
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

IMPORTANT: Naturally incorporate the company's description, values, and mission throughout the job description to help candidates understand the company culture, purpose, and what makes this opportunity unique. Use these elements to make the role more compelling and authentic.

Make it startup-appropriate - emphasize growth, impact, equity, and learning opportunities.
Format as clean markdown with proper headings.
"""


HIRING_CHECKLIST_PROMPT = """
Create a comprehensive hiring checklist for a startup hiring this role.

Company: {company_name} ({company_size}, {company_stage})
Company Description: {company_description}
Company Values: {company_values}
Company Mission: {company_mission}
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
Company Description: {company_description}
Company Values: {company_values}
Company Mission: {company_mission}
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
- Description: {company_description}
- Values: {company_values}
- Mission: {company_mission}
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
Company Description: {company_description}
Company Values: {company_values}
Company Mission: {company_mission}
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
