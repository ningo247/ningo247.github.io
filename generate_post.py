import google.generativeai as genai
import os
import json
import sys
from datetime import datetime
import urllib.parse
import re

def slugify(text):
    text = text.lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    topic = os.environ.get("TOPIC")
    
    if not api_key or not topic:
        print("Missing API Key or Topic")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = f"""
    Write a blog post about {topic}. 
    Return the result in JSON format with these exact keys:
    - title: A catchy title
    - description: A one-sentence SEO description
    - categories: ['Recipes']
    - tags: 3-5 relevant lowercase tags
    - image_keyword: A single, highly-specific food keyword for an image search 
      (e.g., if the recipe is Fettuccini Alfredo, use 'fettuccini' or 'alfredo', not just 'food').
    - content: The full markdown body of the post.
    """

    try:
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        # filename = f"_posts/{date_str}-ai-generated.md"
            
        slug = slugify(data['title'])
        filename = f"_posts/{date_str}-{slug}.md"

       # 1. Define the image URL (using the fixed 16:9 ratio we discussed)
        # img_kw = data.get('image_keyword', 'cooking')
        # img_url = f"https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&h=400&q=80&q={img_kw}"
        
        img_kw = data.get('image_keyword', 'cooking')
        # We use a timestamp to 'bust' the cache and get a new image each time
        sig = int(datetime.now().timestamp())

        # This is the 2026 'hack' for dynamic Unsplash images:
        img_url = f"https://images.unsplash.com/photo-1?auto=format&fit=crop&w=1200&h=600&q=80&sig={sig}&{urllib.parse.quote(img_kw)}"
        
        # 2. Build the Clean Frontmatter (No more 'image:' key here)
        frontmatter = (
            "---\n"
            "layout: post\n"
            f"date: {date_str}\n"
            f"title: \"{data['title']}\"\n"
            f"description: \"{data['description']}\"\n"
            f"categories: {data['categories']}\n"
            f"tags: {data['tags']}\n"
            "---\n\n"
        )

        # 3. Inject the Image at the start of the Content
        # We use the 'align-right' class for that nice wrap-around effect
        image_html = f'<img src="{img_url}" class="align-right" alt="{data["title"]} photo">\n\n'
        
        full_body = frontmatter + image_html + data['content']

        with open(filename, "w") as f:
            f.write(full_body)
        print(f"Successfully created {filename}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()