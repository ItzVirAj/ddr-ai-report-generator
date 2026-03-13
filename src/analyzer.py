from src.schema import validate_ddr
import json
import os
import textwrap
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai

from src.normalizer import build_llm_context
from src.severity_engine import evaluate_severity


# Load .env file from root folder
load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        ".env"
    )
)


class DDRAnalyzer:

    def __init__(self, model: str = "gemini-3.1-flash-lite-preview"):
        """
        Initialize the Code Analyzer with Gemini API.
        """

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in your .env file."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

        # prevent extremely large prompts
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
    # prompt size protection
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

        # remove ```json blocks
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
        thermal_text: str
    ) -> Dict[str, Any]:
        """
        Generate DDR structured report from inspection + thermal documents.
        """

        context = build_llm_context(inspection_text, thermal_text)

        inspection_clean = self._truncate(context["inspection_clean"])
        thermal_clean = self._truncate(context["thermal_clean"])

        inspection_obs = context.get("inspection_observations", [])
        thermal_obs = context.get("thermal_observations", [])

        # -------------------------------------------------------
        # FIXED PROMPT — enforces room separation + thermal linking
        # -------------------------------------------------------

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
           - If thermal report confirms moisture in that area → write the thermal reading or note
           - If thermal report does NOT mention that area → write "Not confirmed by thermal scan"
           - Never leave it blank

        3. source field:
           - "inspection" → only in inspection report
           - "thermal" → only in thermal report
           - "both" → confirmed in both reports

        4. related_image_ids → leave as empty list []
           (images will be mapped automatically after analysis)

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
    # ------------------------------------------------------------------
    # EXISTING CODE ANALYSIS METHODS (UNCHANGED)
    # ------------------------------------------------------------------

    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:

        prompt = textwrap.dedent(f"""
        You are an expert code reviewer.

        Analyze the following {language} code and provide:

        1. Bugs
        2. Security Issues
        3. Code Quality improvements
        4. Performance improvements
        5. Best Practices

        Code:

        ```{language}
        {code}
        ```
        """)

        try:

            result = self._generate(prompt)

            return {
                "success": True,
                "analysis": result,
                "language": language
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    # ---------------------------------------------------------

    def suggest_fixes(self, code: str, language: str, issue: str) -> Dict[str, Any]:

        prompt = textwrap.dedent(f"""
        Issue:
        {issue}

        Code:

        ```{language}
        {code}
        ```

        Provide corrected code and explanation.
        """)

        try:

            result = self._generate(prompt)

            return {
                "success": True,
                "suggestion": result,
                "language": language
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    # ---------------------------------------------------------

    def explain_code(self, code: str, language: str) -> Dict[str, Any]:

        prompt = textwrap.dedent(f"""
        Explain the following {language} code clearly.

        ```{language}
        {code}
        ```
        """)

        try:

            result = self._generate(prompt)

            return {
                "success": True,
                "explanation": result,
                "language": language
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    # ---------------------------------------------------------

    def check_complexity(self, code: str, language: str) -> Dict[str, Any]:

        prompt = textwrap.dedent(f"""
        Analyze the complexity of the following {language} code.

        ```{language}
        {code}
        ```
        """)

        try:

            result = self._generate(prompt)

            return {
                "success": True,
                "complexity_analysis": result,
                "language": language
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    # ---------------------------------------------------------

    def generate_tests(self, code: str, language: str) -> Dict[str, Any]:

        prompt = textwrap.dedent(f"""
        Generate unit tests for the following {language} code.

        ```{language}
        {code}
        ```
        """)

        try:

            result = self._generate(prompt)

            return {
                "success": True,
                "tests": result,
                "language": language
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    # ---------------------------------------------------------

    def refactor_code(self, code: str, language: str) -> Dict[str, Any]:

        prompt = textwrap.dedent(f"""
        Refactor the following {language} code.

        ```{language}
        {code}
        ```
        """)

        try:

            result = self._generate(prompt)

            return {
                "success": True,
                "refactored_code": result,
                "language": language
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }