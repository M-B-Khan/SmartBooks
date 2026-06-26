import re
from difflib import SequenceMatcher


# Keyword map — each category has strong signal words
CATEGORY_KEYWORDS = {
    'Software & Subscriptions': [
        'software', 'subscription', 'saas', 'license', 'app', 'plugin',
        'github', 'aws', 'hosting', 'domain', 'cloud', 'zoom', 'slack',
        'notion', 'figma', 'adobe', 'microsoft', 'google workspace',
        'digitalocean', 'heroku', 'netlify', 'vercel', 'chatgpt', 'openai'
    ],
    'Office Supplies': [
        'stationery', 'paper', 'pen', 'pencil', 'notebook', 'printer',
        'ink', 'toner', 'stapler', 'folder', 'office', 'supplies',
        'whiteboard', 'marker', 'envelope', 'tape', 'scissors'
    ],
    'Travel & Transport': [
        'fuel', 'petrol', 'diesel', 'uber', 'careem', 'taxi', 'flight',
        'airline', 'hotel', 'accommodation', 'transport', 'travel',
        'bus', 'train', 'toll', 'parking', 'visa', 'passport'
    ],
    'Food & Entertainment': [
        'food', 'lunch', 'dinner', 'breakfast', 'restaurant', 'cafe',
        'coffee', 'meal', 'snack', 'catering', 'entertainment', 'event',
        'party', 'celebration', 'pizza', 'biryani', 'tea', 'drinks'
    ],
    'Utilities': [
        'electricity', 'wapda', 'internet', 'broadband', 'wifi', 'water',
        'gas', 'utility', 'bill', 'ptcl', 'zong', 'jazz', 'ufone',
        'telenor', 'phone', 'mobile', 'sui gas'
    ],
    'Salaries & Payroll': [
        'salary', 'salaries', 'payroll', 'wages', 'wage', 'staff',
        'employee', 'bonus', 'allowance', 'overtime', 'compensation',
        'hiring', 'freelancer', 'contractor'
    ],
    'Marketing & Advertising': [
        'marketing', 'advertising', 'ad', 'ads', 'facebook', 'instagram',
        'google ads', 'seo', 'campaign', 'promotion', 'banner',
        'flyer', 'branding', 'logo', 'social media', 'influencer'
    ],
    'Equipment & Hardware': [
        'laptop', 'computer', 'pc', 'monitor', 'keyboard', 'mouse',
        'phone', 'mobile', 'tablet', 'ipad', 'charger', 'cable',
        'hardware', 'equipment', 'printer', 'scanner', 'camera',
        'headphones', 'speaker', 'router', 'switch', 'server'
    ],
    'Professional Services': [
        'legal', 'lawyer', 'attorney', 'accounting', 'accountant',
        'consultant', 'consulting', 'audit', 'tax', 'advisory',
        'professional', 'services', 'notary', 'registration', 'filing'
    ],
    'Miscellaneous': [
        'other', 'misc', 'miscellaneous', 'general', 'various'
    ],
}


def preprocess(text: str) -> str:
    """Lowercase and remove special characters."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text.strip()


def categorize_expense(title: str, description: str = '') -> dict:
    """
    Categorizes an expense using keyword matching + fuzzy similarity.

    Returns:
        {
            'category': 'Equipment & Hardware',
            'confidence': 0.92,
            'method': 'keyword'
        }
    """
    # Combine title and description — title weighted more
    combined = preprocess(f'{title} {title} {description}')
    words = combined.split()

    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0.0

        for keyword in keywords:
            keyword = keyword.lower()

            # Exact phrase match in full text (highest weight)
            if keyword in combined:
                score += 1.0

            else:
                # Fuzzy match against each word
                for word in words:
                    similarity = SequenceMatcher(
                        None, keyword, word
                    ).ratio()
                    if similarity > 0.85:
                        score += similarity * 0.6

        scores[category] = score

    # Get best match
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    # Normalize confidence to 0-1 range
    total_score = sum(scores.values())
    confidence = (best_score / total_score) if total_score > 0 else 0

    # Fall back to Miscellaneous if confidence too low
    if confidence < 0.2 or best_score == 0:
        return {
            'category': 'Miscellaneous',
            'confidence': 0.5,
            'method': 'fallback'
        }

    return {
        'category': best_category,
        'confidence': round(confidence, 2),
        'method': 'keyword'
    }