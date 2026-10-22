import re
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
import httpx
from backend.config import settings

logger = logging.getLogger("fetch_relief.intent")

class IntentParserService:
    @classmethod
    async def parse_prompt(cls, user_prompt: str) -> Tuple[Dict[str, Any], str]:
        """
        Interprets natural language emergency request.
        Attempts ASI1 API if configured; otherwise seamlessly runs deterministic rule-based parser.
        Returns:
        - parsed_scenario_data: Dict with extracted entities, overrides, and action.
        - provider_label: "ASI1 API (asi1-mini)" or "Local Deterministic NLP Parser"
        """
        # Try live ASI1 API if key is present
        if settings.ASI_ONE_API_KEY:
            try:
                parsed_data = await cls._call_asi1_api(user_prompt)
                if parsed_data:
                    return parsed_data, f"ASI1 API ({settings.ASI1_MODEL})"
            except Exception as e:
                logger.warning(f"ASI1 API call failed, falling back to local parser: {e}")

        # Deterministic Fallback Parser
        parsed_data = cls._deterministic_fallback_parser(user_prompt)
        return parsed_data, "Local Deterministic NLP Parser (Offline Fallback)"

    @classmethod
    async def _call_asi1_api(cls, prompt: str) -> Optional[Dict[str, Any]]:
        url = f"{settings.ASI1_BASE_URL.rstrip('/')}/chat/completions"
        system_prompt = (
            "You are an emergency response intent parser for Fetch Relief. "
            "Extract structured data from the user's disaster response query. "
            "Output ONLY valid JSON with keys: "
            "'action' ('simulate', 'status', 'reset'), "
            "'incident_type' (e.g. 'flood', 'earthquake'), "
            "'target_zones' (list of strings, e.g. ['North Zone', 'River Zone']), "
            "'inventory_overrides' (dict of resource: quantity, e.g. {'food_kit': 500, 'water_unit': 300}), "
            "'vehicle_count' (integer or null), "
            "'focus' (string summary of intent)."
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.ASI_ONE_API_KEY}"
        }
        payload = {
            "model": settings.ASI1_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 400
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                result = resp.json()
                content = result["choices"][0]["message"]["content"].strip()
                # Clean potential markdown wrapping
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                return json.loads(content.strip())
        return None

    @classmethod
    def _deterministic_fallback_parser(cls, prompt: str) -> Dict[str, Any]:
        """
        Rule-based deterministic entity extractor.
        Accurately parses disaster types, locations, and resource quantities.
        """
        text = prompt.lower()

        # Action detection
        action = "simulate"
        if any(w in text for w in ["reset", "restart", "restore"]):
            action = "reset"
        elif any(w in text for w in ["status", "inventory", "stock", "check"]):
            action = "status"

        # Incident type
        incident_type = "flood"
        if "earthquake" in text:
            incident_type = "earthquake"
        elif "storm" in text or "hurricane" in text or "cyclone" in text:
            incident_type = "severe_storm"
        elif "fire" in text or "wildfire" in text:
            incident_type = "wildfire"

        # Target zones
        target_zones = []
        if "north" in text:
            target_zones.append("North Zone")
        if "river" in text:
            target_zones.append("River Zone")
        if "market" in text:
            target_zones.append("Market Zone")
        if not target_zones:
            target_zones = ["North Zone", "River Zone", "Market Zone"]

        # Inventory overrides extraction using regex
        inventory_overrides: Dict[str, int] = {}

        # Look for numbers preceding resource keywords
        food_match = re.search(r"(\d+)\s*(?:food|ration|meals)", text)
        if food_match:
            inventory_overrides["food_kit"] = int(food_match.group(1))

        water_match = re.search(r"(\d+)\s*(?:water|liters?|jugs?)", text)
        if water_match:
            inventory_overrides["water_unit"] = int(water_match.group(1))

        med_match = re.search(r"(\d+)\s*(?:first[- ]aid|medical|kits|trauma)", text)
        if med_match:
            inventory_overrides["first_aid_kit"] = int(med_match.group(1))

        blanket_match = re.search(r"(\d+)\s*(?:blankets?|thermal)", text)
        if blanket_match:
            inventory_overrides["blanket"] = int(blanket_match.group(1))

        gen_match = re.search(r"(\d+)\s*(?:generators?|power)", text)
        if gen_match:
            inventory_overrides["generator"] = int(gen_match.group(1))

        veh_match = re.search(r"(\d+)\s*(?:vehicles?|trucks?|vans?)", text)
        vehicle_count = int(veh_match.group(1)) if veh_match else None

        return {
            "action": action,
            "incident_type": incident_type,
            "target_zones": target_zones,
            "inventory_overrides": inventory_overrides,
            "vehicle_count": vehicle_count,
            "focus": f"Simulated {incident_type} relief across {', '.join(target_zones)}"
        }
