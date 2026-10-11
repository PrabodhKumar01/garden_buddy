"""Structured gardening knowledge base covering plants, watering, soil, pests, and seasons."""

from typing import Any, Dict, List

GARDENING_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    # --- TOMATO ---
    {
        "id": "tomato_watering",
        "title": "Tomato Watering Guidelines",
        "category": "watering",
        "plant": "tomato",
        "keywords": ["tomato", "water", "watering", "moisture", "rain", "blossom end rot", "cracking"],
        "content": (
            "Tomatoes require consistent, deep watering rather than frequent light sprinkling. "
            "Always check soil moisture 2 inches below the surface before watering. "
            "If significant rain (>5mm) is forecasted within 24 hours, postpone watering to prevent waterlogging and fruit cracking. "
            "Water early in the morning at the base of the plant to keep foliage dry and deter fungal diseases."
        ),
    },
    {
        "id": "tomato_yellow_leaves",
        "title": "Tomato Yellow Leaves Diagnosis & Care",
        "category": "pests",
        "plant": "tomato",
        "keywords": ["tomato", "yellow", "yellowing", "leaves", "chlorosis", "overwatering", "nitrogen", "blight"],
        "content": (
            "Yellowing leaves on tomato plants are most commonly caused by overwatering, poor drainage, or nitrogen deficiency. "
            "If lower leaves turn yellow and soil is soggy, reduce watering immediately. "
            "Prune off lower yellowed leaves near the soil line with clean shears to improve air circulation and prevent early blight. "
            "Ensure the container or garden bed drains freely."
        ),
    },
    {
        "id": "tomato_sunlight_soil",
        "title": "Tomato Sunlight & Soil Requirements",
        "category": "sunlight",
        "plant": "tomato",
        "keywords": ["tomato", "sun", "sunlight", "soil", "drainage", "fertilizer", "staking"],
        "content": (
            "Tomatoes thrive in full sun, needing at least 6 to 8 hours of direct sunlight daily. "
            "They prefer rich, loamy, well-draining soil with a pH between 6.2 and 6.8. "
            "Stake or cage plants early to keep fruit off the ground and reduce exposure to soil-borne pathogens."
        ),
    },

    # --- CORIANDER / CILANTRO ---
    {
        "id": "coriander_care_harvest",
        "title": "Coriander Harvesting and Bolting Prevention",
        "category": "care",
        "plant": "coriander",
        "keywords": ["coriander", "cilantro", "harvest", "leaves", "bolting", "heat", "trim"],
        "content": (
            "Harvest coriander frequently once stems reach 6 inches tall by trimming outer leaves, allowing inner leaves to keep growing. "
            "Coriander bolts (flowers prematurely) when exposed to high heat (>25°C) or drought stress. "
            "Keep soil consistently moist and provide partial shade during hot afternoons to prolong the harvest window."
        ),
    },
    {
        "id": "coriander_watering",
        "title": "Coriander Watering & Soil Needs",
        "category": "watering",
        "plant": "coriander",
        "keywords": ["coriander", "cilantro", "water", "watering", "soil", "drainage"],
        "content": (
            "Coriander has shallow root systems and prefers moist but well-drained soil. "
            "Water regularly when the top inch of soil feels dry. Avoid soggy waterlogged conditions which induce root rot."
        ),
    },

    # --- SPINACH ---
    {
        "id": "spinach_planting_care",
        "title": "Spinach Planting & Cool Weather Requirements",
        "category": "planting",
        "plant": "spinach",
        "keywords": ["spinach", "planting", "cool", "season", "harvest", "temperature", "seeds"],
        "content": (
            "Spinach is a cool-weather crop that grows best in temperatures between 10°C and 20°C. "
            "Sow seeds 1/2 inch deep in soil rich in organic matter. "
            "Harvest outer leaves as baby spinach or harvest the whole plant before warm weather triggers bolting. "
            "Ideal for early spring or autumn plantings."
        ),
    },
    {
        "id": "spinach_watering_soil",
        "title": "Spinach Watering & Soil Moisture",
        "category": "watering",
        "plant": "spinach",
        "keywords": ["spinach", "water", "soil", "nitrogen", "moisture"],
        "content": (
            "Spinach needs consistent moisture to produce tender, non-bitter leaves. "
            "Keep the soil uniformly damp with mulching. "
            "Avoid letting the bed dry out completely, but ensure drainage is adequate to prevent crown rot."
        ),
    },

    # --- MINT ---
    {
        "id": "mint_care_containment",
        "title": "Mint Care and Container Growing",
        "category": "care",
        "plant": "mint",
        "keywords": ["mint", "container", "invasive", "roots", "prune", "harvest"],
        "content": (
            "Mint is an aggressive, fast-spreading perennial herb with vigorous underground runners. "
            "Always grow mint in a standalone pot or container to prevent it from overtaking garden beds. "
            "Pinch back stem tips regularly to encourage bushy growth and prevent leggy flowering."
        ),
    },
    {
        "id": "mint_watering_sun",
        "title": "Mint Sunlight & Moisture Needs",
        "category": "sunlight",
        "plant": "mint",
        "keywords": ["mint", "water", "sun", "shade", "moist"],
        "content": (
            "Mint prefers moist, rich soil and thrives in partial shade to full sun. "
            "Water whenever the top inch of soil is dry; mint wilts rapidly if allowed to dry out, but bounces back quickly once watered."
        ),
    },

    # --- GENERAL WATERING RULES ---
    {
        "id": "general_weather_rain_watering",
        "title": "Gardening Decisions Around Weather & Rain",
        "category": "watering",
        "plant": None,
        "keywords": ["rain", "weather", "watering", "forecast", "tomorrow", "storm", "wet"],
        "content": (
            "When rainfall is forecasted within the next 24 to 48 hours with high probability (>=40%), "
            "withhold irrigation for established outdoor plants to conserve water and prevent root asphyxiation. "
            "Before heavy rain, clear drainage pathways, stake top-heavy plants, and harvest ripe vegetables to prevent split skins."
        ),
    },
    {
        "id": "general_soil_moisture_finger_test",
        "title": "Soil Moisture Finger Check Method",
        "category": "soil",
        "plant": None,
        "keywords": ["soil", "moisture", "finger", "check", "test", "dry", "wet", "damp"],
        "content": (
            "Perform the finger test before watering: insert your index finger 1 to 2 inches into the soil. "
            "If soil feels cool and damp, delay watering. If it feels completely dry and warm, give a thorough soaking. "
            "Soil surface appearance is often deceptive; sub-surface moisture is what plant roots depend on."
        ),
    },

    # --- PESTS & DISEASES ---
    {
        "id": "general_pest_inspection",
        "title": "Routine Garden Inspection & Organic Pest Control",
        "category": "pests",
        "plant": None,
        "keywords": ["pest", "aphids", "inspection", "bugs", "leaves", "underside", "organic", "neem"],
        "content": (
            "Inspect the undersides of leaves and new tender growth weekly for aphids, spider mites, or caterpillar eggs. "
            "Dislodge early aphid colonies with a strong jet of water from the hose. "
            "For persistent organic control, spray with insecticidal soap or diluted neem oil during cooler evening hours."
        ),
    },
    {
        "id": "general_powdery_mildew",
        "title": "Preventing & Managing Powdery Mildew",
        "category": "pests",
        "plant": None,
        "keywords": ["mildew", "powdery", "white", "fungus", "air", "circulation", "prune"],
        "content": (
            "Powdery mildew presents as white flour-like coating on upper leaf surfaces, thriving in warm days with humid nights. "
            "Prevent by watering soil rather than leaves, providing good plant spacing, and pruning dense foliage for air flow. "
            "Remove heavily infected leaves and discard in household trash (do not compost diseased material)."
        ),
    },

    # --- SEASONAL GARDENING ---
    {
        "id": "general_seasonal_prep",
        "title": "Seasonal Garden Preparation & Mulching",
        "category": "seasonal",
        "plant": None,
        "keywords": ["mulch", "seasonal", "summer", "winter", "temperature", "weeds", "soil"],
        "content": (
            "Apply a 2-inch layer of organic mulch (straw, bark, or shredded leaves) around garden beds. "
            "Mulch insulates plant roots against extreme temperature swings, retains vital soil moisture during dry spells, "
            "and suppresses competing weeds."
        ),
    },
]

