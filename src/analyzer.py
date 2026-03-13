import os
import textwrap
from typing import Dict, Any
from dotenv import load_dotenv

import google.genai as genai

# Load .env file from root folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class CodeAnalyzer:
    def __init__(self, model: str = "gemini-3.0-flash"):
        """
        Initialize the Code Analyzer with Gemini API.

        Expects GEMINI_API_KEY to be set in the .env file at root.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in your .env file at the root of the project."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _generate(self, prompt: str) -> str:
        """Internal helper to call Gemini and return plain text."""
        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return resp.text or "No response generated."

    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        prompt = textwrap.dedent(
            f"""
            You are an expert code reviewer. Analyze the following {language} code and provide:

            1. Bugs: List any bugs or errors in the code
            2. Security Issues: Identify potential security vulnerabilities
            3. Code Quality: Suggestions for improving code quality
            4. Performance: Performance optimization suggestions
            5. Best Practices: Recommendations for following best practices

            Format your response as a structured analysis with clear headings.

            Code to analyze:
            ```{language}
            {code}
            ```

            Provide detailed, actionable feedback.
            """
        ).strip()

        try:
            result = self._generate(prompt)
            return {"success": True, "analysis": result, "language": language}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def suggest_fixes(self, code: str, language: str, issue: str) -> Dict[str, Any]:
        prompt = textwrap.dedent(
            f"""
            You are an expert programmer. Given the following {language} code and the issue described,
            provide a corrected version of the code with explanations.

            Issue: {issue}

            Original Code:
            ```{language}
            {code}
            ```

            Please provide:
            1. Explanation of the issue
            2. Corrected code
            3. Explanation of the fix

            Format the corrected code clearly within code blocks.
            """
        ).strip()

        try:
            result = self._generate(prompt)
            return {"success": True, "suggestion": result, "language": language}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def explain_code(self, code: str, language: str) -> Dict[str, Any]:
        prompt = textwrap.dedent(
            f"""
            You are an expert programming instructor. Explain the following {language} code in detail:

            ```{language}
            {code}
            ```

            Provide:
            1. Overall purpose of the code
            2. Line-by-line or block-by-block explanation
            3. Key concepts used
            4. Potential use cases

            Make the explanation clear and educational.
            """
        ).strip()

        try:
            result = self._generate(prompt)
            return {"success": True, "explanation": result, "language": language}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_complexity(self, code: str, language: str) -> Dict[str, Any]:
        prompt = textwrap.dedent(
            f"""
            Analyze the complexity of the following {language} code:

            ```{language}
            {code}
            ```

            Provide:
            1. Cyclomatic complexity assessment
            2. Time complexity analysis
            3. Space complexity analysis
            4. Maintainability score (1-10)
            5. Suggestions to reduce complexity

            Be specific and technical in your analysis.
            """
        ).strip()

        try:
            result = self._generate(prompt)
            return {"success": True, "complexity_analysis": result, "language": language}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_tests(self, code: str, language: str) -> Dict[str, Any]:
        prompt = textwrap.dedent(
            f"""
            Generate comprehensive unit tests for the following {language} code:

            ```{language}
            {code}
            ```

            Provide:
            1. Test cases covering normal scenarios
            2. Edge cases
            3. Error handling tests
            4. Use the appropriate testing framework for {language}

            Format the tests as runnable code with comments.
            """
        ).strip()

        try:
            result = self._generate(prompt)
            return {"success": True, "tests": result, "language": language}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def refactor_code(self, code: str, language: str) -> Dict[str, Any]:
        prompt = textwrap.dedent(
            f"""
            Refactor the following {language} code to improve its quality:

            ```{language}
            {code}
            ```

            Focus on:
            1. Code readability
            2. Maintainability
            3. Performance
            4. Following {language} best practices and idioms

            Provide:
            1. Refactored code
            2. Explanation of changes made
            3. Benefits of the refactoring
            """
        ).strip()

        try:
            result = self._generate(prompt)
            return {"success": True, "refactored_code": result, "language": language}
        except Exception as e:
            return {"success": False, "error": str(e)}