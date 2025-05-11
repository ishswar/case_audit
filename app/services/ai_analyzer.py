from google import genai
import json
import re
from ..models.audit import AuditReport, AuditRatings, CaseInfo

class AIAnalyzer:
    def __init__(self, project_id: str = "webfocus-devops", location: str = "global"):
        self.project_id = project_id
        self.location = location
        try:
            # Configure with Vertex AI
            genai.configure(
                api_key=None,  # Will use ADC
                project_id=project_id,
                location=location,
                vertexai=True,
            )
            self.model = genai.GenerativeModel('gemini-2.0-flash-001')
        except Exception as e:
            print(f"Error configuring Google AI API: {e}")
            self.model = None

    def _clean_json_response(self, text: str) -> dict:
        """Clean and extract the JSON response directly as a dictionary."""
        # Remove any markdown formatting
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Try direct JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Handle common JSON formatting issues
            try:
                # Try to find just the JSON object in the response
                json_match = re.search(r'(\{.*\})', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
            
            # More aggressive cleaning
            cleaned_text = text
            # Replace escaped quotes with simple quotes
            cleaned_text = cleaned_text.replace('\\"', '"')
            # Ensure property names are properly quoted
            cleaned_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned_text)
            
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse AI model response as JSON: {e}\nResponse: {text}")

    def analyze_case(self, case_content: str, case_info: CaseInfo) -> AuditReport:
        """Analyze the case and generate audit report with ratings."""
        
        prompt = f"""
        Please evaluate the quality of support for this TIBCO support case. 
        Analyze the case content below from a quality assurance perspective, focus on:

        1. Initial Response - How timely and effective was the initial response?
        2. Problem Diagnosis - How effective was the approach to diagnosing the issue?
        3. Technical Accuracy - How accurate and relevant was the technical guidance provided?
        4. Solution Quality - How effective was the solution provided?
        5. Communication - How clear, professional, and timely was the communication?
        6. Overall Experience - How would you rate the customer's overall experience?

        Rate each category from 1-5 (5 being best), and provide brief feedback for each category.
        Also provide an overall assessment and list 3-5 specific recommendations for improvement.

        Format your recommendations as a numbered list and make them specific and actionable.
        For example:
        1. Be more proactive in follow-ups
        2. Document steps taken in more detail
        3. Include specific steps for the customer to troubleshoot
        4. Escalate to engineering sooner when initial efforts aren't working
        5. Provide documentation links with each response

        Format your analysis as valid JSON like this:
        {{
          "ratings": {{
            "initial_response": 3,
            "problem_diagnosis": 4,
            "technical_accuracy": 4,
            "solution_quality": 3,
            "communication": 3,
            "overall_experience": 3
          }},
          "initial_response_feedback": "The initial response was prompt but could be improved by...",
          "problem_diagnosis_feedback": "The problem diagnosis was thorough and correctly identified that...",
          "technical_accuracy_feedback": "The technical analysis provided was mostly accurate...",
          "solution_feedback": "The solution was effective but took longer than necessary to...",
          "communication_feedback": "Communication was regular but could be enhanced by...",
          "overall_feedback": "Overall, this was a decent support case, but improvements could be made in...",
          "recommendations": "1. Improve the initial response by personalizing it more. 2. Provide clearer steps for diagnosis. 3. Follow up more proactively. 4. Include links to relevant documentation. 5. Escalate complex issues more quickly."
        }}

        Case details:
        Product: {case_info.product_name} {case_info.product_version}
        Subject: {case_info.subject}
        
        Case contents:
        {case_content[:3000]}
        """

        # Check if model is available
        if self.model is None:
            raise RuntimeError("Google AI model not available. Authentication may have failed.")
            
        # Call the Gemini API
        print("Processing AI response...")
        response = self.model.generate_content(prompt)
        
        # Parse the response
        response_text = response.text
        result = self._clean_json_response(response_text)
        
        # Create and return AuditReport
        return AuditReport(
            case_info=case_info,
            ratings=AuditRatings(
                initial_response=result.get("ratings", {}).get("initial_response", 3),
                problem_diagnosis=result.get("ratings", {}).get("problem_diagnosis", 3),
                technical_accuracy=result.get("ratings", {}).get("technical_accuracy", 3),
                solution_quality=result.get("ratings", {}).get("solution_quality", 3),
                communication=result.get("ratings", {}).get("communication", 3),
                overall_experience=result.get("ratings", {}).get("overall_experience", 3)
            ),
            initial_response_feedback=result.get("initial_response_feedback", ""),
            problem_diagnosis_feedback=result.get("problem_diagnosis_feedback", ""),
            technical_accuracy_feedback=result.get("technical_accuracy_feedback", ""),
            solution_feedback=result.get("solution_feedback", ""),
            communication_feedback=result.get("communication_feedback", ""),
            overall_feedback=result.get("overall_feedback", ""),
            recommendations=result.get("recommendations", "")
        ) 