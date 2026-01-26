"""
Sample test data for Vectara API Test Suite.

Provides reusable test documents and queries for consistent testing.
"""

# Sample documents covering different topics and formats
SAMPLE_DOCUMENTS = [
    {
        "id": "tech_ai_001",
        "title": "Introduction to Artificial Intelligence",
        "text": """
        Artificial intelligence (AI) is the simulation of human intelligence processes
        by machines, especially computer systems. These processes include learning,
        reasoning, and self-correction. AI is being applied across many industries
        including healthcare, finance, manufacturing, and transportation.

        Machine learning, a subset of AI, enables systems to automatically learn and
        improve from experience without being explicitly programmed. Deep learning,
        which uses neural networks with many layers, has achieved remarkable results
        in image recognition, natural language processing, and game playing.
        """,
        "metadata": {
            "category": "technology",
            "topic": "artificial_intelligence",
            "difficulty": "beginner",
        },
    },
    {
        "id": "tech_db_001",
        "title": "Understanding Vector Databases",
        "text": """
        Vector databases are specialized database systems designed to store and query
        high-dimensional vectors efficiently. Unlike traditional databases that use
        exact matching, vector databases use similarity search to find the most
        relevant results based on semantic meaning.

        These databases are essential for modern AI applications including:
        - Semantic search engines
        - Recommendation systems
        - Image and video search
        - Natural language processing

        Popular vector databases include Vectara, Pinecone, Weaviate, and Milvus.
        Each offers different features for scaling and query optimization.
        """,
        "metadata": {
            "category": "technology",
            "topic": "databases",
            "difficulty": "intermediate",
        },
    },
    {
        "id": "science_climate_001",
        "title": "Climate Change Overview",
        "text": """
        Climate change refers to long-term shifts in global temperatures and weather
        patterns. While natural factors can cause climate variations, human activities
        have been the main driver since the Industrial Revolution.

        The primary cause is the burning of fossil fuels like coal, oil, and gas,
        which releases greenhouse gases into the atmosphere. These gases trap heat,
        causing the planet to warm - a phenomenon known as the greenhouse effect.

        Effects of climate change include rising sea levels, more frequent extreme
        weather events, changes in precipitation patterns, and impacts on ecosystems.
        """,
        "metadata": {
            "category": "science",
            "topic": "climate",
            "difficulty": "beginner",
        },
    },
    {
        "id": "business_startup_001",
        "title": "Startup Funding Stages",
        "text": """
        Startup companies typically go through several funding stages as they grow:

        Pre-seed: Initial funding from founders, friends, and family. Used to
        develop the initial idea and create a minimum viable product.

        Seed: First significant external funding, often from angel investors.
        Used to validate the product-market fit and early growth.

        Series A: Venture capital funding for companies with proven traction.
        Used to scale operations and expand the team.

        Series B and beyond: Larger funding rounds for companies demonstrating
        strong growth, used for market expansion and scaling.
        """,
        "metadata": {
            "category": "business",
            "topic": "funding",
            "difficulty": "intermediate",
        },
    },
    {
        "id": "health_nutrition_001",
        "title": "Basics of Balanced Nutrition",
        "text": """
        A balanced diet provides all the nutrients your body needs to function
        properly. The main components include:

        Macronutrients:
        - Carbohydrates: Primary energy source (grains, fruits, vegetables)
        - Proteins: Building blocks for muscles and tissues (meat, fish, legumes)
        - Fats: Essential for hormone production and nutrient absorption

        Micronutrients:
        - Vitamins: Organic compounds needed in small amounts
        - Minerals: Inorganic elements like calcium, iron, and zinc

        Hydration is also crucial - adults should aim for about 8 glasses of
        water per day, though needs vary based on activity and climate.
        """,
        "metadata": {
            "category": "health",
            "topic": "nutrition",
            "difficulty": "beginner",
        },
    },
]

# Sample queries for testing search functionality
SAMPLE_QUERIES = [
    {
        "query": "What is artificial intelligence?",
        "expected_topics": ["artificial_intelligence"],
        "description": "Basic AI concept query",
    },
    {
        "query": "How do vector databases work for semantic search?",
        "expected_topics": ["databases"],
        "description": "Technical database query",
    },
    {
        "query": "What causes global warming?",
        "expected_topics": ["climate"],
        "description": "Climate science query",
    },
    {
        "query": "How do startups raise money?",
        "expected_topics": ["funding"],
        "description": "Business funding query",
    },
    {
        "query": "What should I eat for a healthy diet?",
        "expected_topics": ["nutrition"],
        "description": "Health nutrition query",
    },
    {
        "query": "machine learning neural networks deep learning",
        "expected_topics": ["artificial_intelligence"],
        "description": "Technical ML terms",
    },
    {
        "query": "greenhouse gases emissions temperature",
        "expected_topics": ["climate"],
        "description": "Climate keywords",
    },
]

# Queries that should return minimal or no results
NEGATIVE_QUERIES = [
    "quantum teleportation through medieval castles",
    "underwater basket weaving techniques from Mars",
    "ancient Egyptian smartphone repair methods",
]

# Special character test strings
SPECIAL_CHARACTER_TESTS = [
    "Testing 'single' and \"double\" quotes",
    "Unicode: café, naïve, résumé, 日本語, 中文",
    "Symbols: @#$%^&*()_+-=[]{}|;':\",./<>?",
    "Newlines:\nLine 1\nLine 2\nLine 3",
    "Tabs:\tColumn1\tColumn2\tColumn3",
    "HTML entities: &amp; &lt; &gt; &quot;",
    "Math: 2 + 2 = 4, x² + y² = r², ∑(n=1 to ∞)",
]
