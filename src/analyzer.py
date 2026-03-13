# src/analyzer.py

from src.schema import validate_ddr
import json
import os
import textwrap
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai

from src.normalizer import build_llm_context
from src.severity_engine import evaluate_severity


load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        ".env"
    )
)


class DDRAnalyzer:

    def __init__(self, model: str = "gemini-3-flash-preview"):

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in your .env file."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_chars = 12000

    # ---------------------------------------------------------
    # Gemini wrapper
    # ---------------------------------------------------------

    def _generate(self, prompt: str) -> str:

        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return resp.text or ""

    # ---------------------------------------------------------
    # Prompt size protection
    # ---------------------------------------------------------

    def _truncate(self, text: str) -> str:

        if not text:
            return ""

        if len(text) > self.max_chars:
            return text[:self.max_chars]

        return text

    # ---------------------------------------------------------
    # Gemini JSON cleanup
    # ---------------------------------------------------------

    def _clean_json(self, text: str) -> str:

        text = text.strip()

        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]

        text = text.replace("json", "", 1).strip()

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    # ------------------------------------------------------------------
    # DDR DOCUMENT ANALYSIS
    # ------------------------------------------------------------------

    def analyze_documents(
        self,
        inspection_text: str,
        thermal_text: str,
        inspection_images: List[Dict] = None,
        thermal_images: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate DDR structured report from inspection + thermal documents.
        Passes image metadata to Gemini for accurate image assignment.
        """

        inspection_images = inspection_images or []
        thermal_images = thermal_images or []

        context = build_llm_context(inspection_text, thermal_text)

        inspection_clean = self._truncate(context["inspection_clean"])
        thermal_clean = self._truncate(context["thermal_clean"])

        inspection_obs = context.get("inspection_observations", [])
        thermal_obs = context.get("thermal_observations", [])

        # build image reference list for prompt
        inspection_image_refs = [
            f"{img['image_id']} (page {img['page_num']})"
            for img in inspection_images
            if img.get("image_id") and img.get("page_num")
        ]

        thermal_image_refs = [
            f"{img['image_id']} (page {img['page_num']})"
            for img in thermal_images
            if img.get("image_id") and img.get("page_num")
        ]

        # limit to avoid overloading prompt
        inspection_image_refs = inspection_image_refs[:60]
        thermal_image_refs = thermal_image_refs[:60]

        prompt = textwrap.dedent(f"""
        You are a professional building diagnostics engineer.

        Analyze the following inspection report and thermal scan report
        and produce a structured Detailed Diagnostic Report (DDR).

        Return ONLY valid JSON. No explanation. No markdown.

        Required JSON schema:

        {{
          "property_issue_summary": "",
          "area_wise_observations": [
            {{
              "area": "",
              "observation": "",
              "source": "inspection | thermal | both",
              "thermal_confirmation": "",
              "related_image_ids": []
            }}
          ],
          "probable_root_cause": [],
          "severity_assessment": {{
            "level": "Low | Medium | High | Critical",
            "reasoning": ""
          }},
          "recommended_actions": [],
          "additional_notes": "",
          "missing_or_unclear_information": ""
        }}

        STRICT RULES — follow exactly:

        1. Each observation must cover ONE ROOM or ONE AREA ONLY.
           - WRONG: "Hall, Bedroom, Kitchen show dampness"
           - CORRECT: Three separate observations for Hall, Bedroom, Kitchen

        2. thermal_confirmation field:
           - If thermal report confirms moisture → write the thermal reading
           - If not confirmed → write "Not confirmed by thermal scan"
           - Never leave it blank

        3. source field:
           - "inspection" → only in inspection report
           - "thermal" → only in thermal report
           - "both" → confirmed in both reports

        4. related_image_ids field — CRITICAL RULE:
           - You are given extracted image IDs with their page numbers
           - Image ID format: label_pPAGE_imgINDEX
             Example: inspection_p3_img2 means page 3, image 2
           - Assign image IDs from the SAME PAGE as the observation area
           - Match images to observations using page proximity and context
           - Assign 2 to 4 images per observation
           - Use ONLY image IDs from the lists provided below
           - Do NOT invent or modify image IDs

        5. Do NOT invent facts. Use only what is in the reports.

        6. If information is missing → write "Not Available"

        7. probable_root_cause must be a list of strings.

        8. recommended_actions must be a list of strings.

        9. THERMAL DATA INTERPRETATION RULE:
           - The thermal report may not label rooms by name
           - It uses image file codes (e.g. RB02380X.JPG)
           - If thermal coldspot readings are below 23°C at skirting level,
             this confirms moisture presence at that zone
           - A hotspot-to-coldspot delta of 3°C or more = confirmed moisture
           - Apply this logic across all room observations where skirting
             dampness is reported in the inspection report
           - Do NOT write "Not confirmed" if thermal scans exist and show
             coldspot patterns consistent with dampness
           - Example thermal_confirmation text:
             "Thermal scan (RB02380X) shows coldspot at 23.4°C with delta
              of 5.4°C confirming subsurface moisture at skirting level."

        Key inspection observations detected:
        {inspection_obs}

        Key thermal indicators detected:
        {thermal_obs}

        AVAILABLE INSPECTION IMAGE IDs — use these for related_image_ids:
        {inspection_image_refs}

        AVAILABLE THERMAL IMAGE IDs — use these for related_image_ids:
        {thermal_image_refs}

        INSPECTION REPORT:
        {inspection_clean}

        THERMAL REPORT:
        {thermal_clean}
        """).strip()

        try:
            response_text = self._generate(prompt)

            if not response_text:
                raise ValueError("Empty response from model")

            cleaned = self._clean_json(response_text)

            try:
                ddr_json = json.loads(cleaned)
            except Exception:
                raise ValueError(
                    "Gemini returned invalid JSON:\n\n" + cleaned[:1000]
                )

            if "area_wise_observations" not in ddr_json:
                ddr_json["area_wise_observations"] = []

            # ensure thermal_confirmation exists on all observations
            for obs in ddr_json["area_wise_observations"]:
                if isinstance(obs, dict):
                    if not obs.get("thermal_confirmation"):
                        obs["thermal_confirmation"] = "Not confirmed by thermal scan"

            if not ddr_json.get("severity_assessment"):
                ddr_json["severity_assessment"] = evaluate_severity(
                    ddr_json.get("area_wise_observations", [])
                )

            validated_ddr = validate_ddr(ddr_json)

            return {
                "success": True,
                "ddr": validated_ddr
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }