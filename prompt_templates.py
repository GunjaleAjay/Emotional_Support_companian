BLOG_IDEA_PROMPT = """
You are an expert content strategist specializing in generating engaging and unique blog post ideas.

I need {num_ideas} blog ideas focused on the topic: "{niche}".  
The ideas should be {include_outline} and have a {tone} tone.

Each blog idea must include:
1. **A compelling, SEO-friendly title**  
2. **A brief description** (2-3 sentences explaining the concept)  
3. **A structured outline** (only if outlines are requested, consisting of 5-7 key points)

### Guidelines:
- Ensure relevance and value for readers interested in "{niche}".
- Ideas should be **specific** and provide actionable insights.
- Content should be **engaging, original, and impactful**.
- **Avoid generic or overly broad topics.**

### Response Format:
1. **Title:** [Your Blog Title]  
   **Description:** [Short description]  
   **Outline:**  
   - [Point 1]  
   - [Point 2]  
   - [Point 3]  
   - [Point 4]  
   - [Point 5] (if applicable)

**RESPOND ONLY WITH THE BLOG IDEAS, WITHOUT ANY EXTRA TEXT.**
"""
