import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class CodeAnalyzer:
    def __init__(self):
        """Initialize the Code Analyzer with Gemini API."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_code(self, code: str, language: str) -> dict:
        """
        Analyze code for bugs, security issues, and improvements.
        
        Args:
            code (str): The source code to analyze
            language (str): Programming language of the code
            
        Returns:
            dict: Analysis results containing bugs, security issues, and suggestions
        """
        prompt = f"""
        You are an expert code reviewer. Analyze the following {language} code and provide:
        
        1. **Bugs**: List any bugs or errors in the code
        2. **Security Issues**: Identify potential security vulnerabilities
        3. **Code Quality**: Suggestions for improving code quality
        4. **Performance**: Performance optimization suggestions
        5. **Best Practices**: Recommendations for following best practices
        
        Format your response as a structured analysis with clear sections.
        
        Code to analyze:
        ```{language}
        {code}
        ```
        
        Provide detailed, actionable feedback.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {
                'success': True,
                'analysis': response.text,
                'language': language
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def suggest_fixes(self, code: str, language: str, issue: str) -> dict:
        """
        Suggest fixes for a specific issue in the code.
        
        Args:
            code (str): The source code
            language (str): Programming language
            issue (str): Specific issue to fix
            
        Returns:
            dict: Suggested fixes and improved code
        """
        prompt = f"""
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
        
        try:
            response = self.model.generate_content(prompt)
            return {
                'success': True,
                'suggestion': response.text,
                'language': language
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def explain_code(self, code: str, language: str) -> dict:
        """
        Provide a detailed explanation of the code.
        
        Args:
            code (str): The source code to explain
            language (str): Programming language
            
        Returns:
            dict: Detailed explanation of the code
        """
        prompt = f"""
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
        
        try:
            response = self.model.generate_content(prompt)
            return {
                'success': True,
                'explanation': response.text,
                'language': language
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_complexity(self, code: str, language: str) -> dict:
        """
        Analyze code complexity and provide metrics.
        
        Args:
            code (str): The source code
            language (str): Programming language
            
        Returns:
            dict: Complexity analysis
        """
        prompt = f"""
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
        
        try:
            response = self.model.generate_content(prompt)
            return {
                'success': True,
                'complexity_analysis': response.text,
                'language': language
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_tests(self, code: str, language: str) -> dict:
        """
        Generate unit tests for the given code.
        
        Args:
            code (str): The source code
            language (str): Programming language
            
        Returns:
            dict: Generated test cases
        """
        prompt = f"""
        Generate comprehensive unit tests for the following {language} code:
        
        ```{language}
        {code}
        ```
        
        Provide:
        1. Test cases covering normal scenarios
        2. Edge cases
        3. Error handling tests
        4. Use appropriate testing framework for {language}
        
        Format the tests as runnable code with comments.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {
                'success': True,
                'tests': response.text,
                'language': language
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def refactor_code(self, code: str, language: str) -> dict:
        """
        Suggest refactored version of the code.
        
        Args:
            code (str): The source code to refactor
            language (str): Programming language
            
        Returns:
            dict: Refactored code with explanations
        """
        prompt = f"""
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
        
        try:
            response = self.model.generate_content(prompt)
            return {
                'success': True,
                'refactored_code': response.text,
                'language': language
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
