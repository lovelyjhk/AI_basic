import openai
import json
import re
from typing import Dict, Any

class AICodeGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
        self.language_templates = {
            'python': {
                'extension': '.py',
                'comment_style': '#',
                'example': 'def solution():\n    pass'
            },
            'javascript': {
                'extension': '.js',
                'comment_style': '//',
                'example': 'function solution() {\n    // code here\n}'
            },
            'java': {
                'extension': '.java',
                'comment_style': '//',
                'example': 'public class Solution {\n    public void solution() {\n        // code here\n    }\n}'
            },
            'cpp': {
                'extension': '.cpp',
                'comment_style': '//',
                'example': '#include <iostream>\nusing namespace std;\n\nint main() {\n    // code here\n    return 0;\n}'
            },
            'c': {
                'extension': '.c',
                'comment_style': '//',
                'example': '#include <stdio.h>\n\nint main() {\n    // code here\n    return 0;\n}'
            },
            'go': {
                'extension': '.go',
                'comment_style': '//',
                'example': 'package main\n\nimport "fmt"\n\nfunc main() {\n    // code here\n}'
            },
            'rust': {
                'extension': '.rs',
                'comment_style': '//',
                'example': 'fn main() {\n    // code here\n}'
            },
            'vlang': {
                'extension': '.v',
                'comment_style': '//',
                'example': 'fn main() {\n    // code here\n}'
            }
        }
    
    def generate_algorithm(self, problem_description: str, language: str, difficulty: str) -> Dict[str, Any]:
        """AI를 사용하여 알고리즘 솔루션 생성"""
        
        # 언어별 템플릿 가져오기
        lang_info = self.language_templates.get(language.lower(), self.language_templates['python'])
        
        # 난이도별 복잡도 가이드
        complexity_guide = {
            'easy': 'Simple and straightforward solution with O(n) or better time complexity',
            'medium': 'Moderately complex solution that may use data structures like hash maps, trees, or require multiple steps',
            'hard': 'Complex solution that may require advanced algorithms, dynamic programming, or sophisticated data structures'
        }
        
        # AI 프롬프트 생성
        prompt = f"""
        Generate a complete algorithm solution for the following problem:
        
        Problem: {problem_description}
        Programming Language: {language}
        Difficulty Level: {difficulty}
        
        Please provide a JSON response with the following structure:
        {{
            "title": "Brief descriptive title for the algorithm",
            "code": "Complete, runnable code solution",
            "explanation": "Detailed explanation of the algorithm approach and logic",
            "time_complexity": "Time complexity analysis (e.g., O(n), O(log n))",
            "space_complexity": "Space complexity analysis (e.g., O(1), O(n))"
        }}
        
        Requirements:
        - Code should be complete and runnable
        - Include appropriate comments
        - Follow best practices for {language}
        - {complexity_guide.get(difficulty, '')}
        - Provide clear variable names and proper formatting
        - Include error handling where appropriate
        
        Make sure the code is optimized and follows the coding standards for {language}.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert programming tutor and algorithm specialist. Generate high-quality, educational algorithm solutions with clear explanations."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # JSON 응답 파싱
            response_text = response.choices[0].message.content.strip()
            
            # JSON 부분만 추출
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # JSON이 없는 경우 기본 파싱
                result = self._parse_fallback_response(response_text, language)
            
            # 필수 필드 검증 및 기본값 설정
            required_fields = ['title', 'code', 'explanation', 'time_complexity', 'space_complexity']
            for field in required_fields:
                if field not in result or not result[field]:
                    result[field] = self._get_default_value(field, problem_description, language)
            
            # 코드 정리 및 포맷팅
            result['code'] = self._clean_code(result['code'], language)
            
            return result
            
        except Exception as e:
            # 에러 발생 시 기본 솔루션 반환
            return self._generate_fallback_solution(problem_description, language, difficulty)
    
    def _parse_fallback_response(self, response_text: str, language: str) -> Dict[str, Any]:
        """JSON 파싱에 실패했을 때 대체 파싱 방법"""
        lines = response_text.split('\n')
        result = {
            'title': 'Algorithm Solution',
            'code': '',
            'explanation': '',
            'time_complexity': 'O(n)',
            'space_complexity': 'O(1)'
        }
        
        # 코드 블록 찾기
        in_code_block = False
        code_lines = []
        
        for line in lines:
            if '```' in line:
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)
        
        if code_lines:
            result['code'] = '\n'.join(code_lines)
        
        return result
    
    def _clean_code(self, code: str, language: str) -> str:
        """코드 정리 및 포맷팅"""
        # 불필요한 백틱 제거
        code = re.sub(r'```\w*\n?', '', code)
        code = re.sub(r'```', '', code)
        
        # 앞뒤 공백 제거
        code = code.strip()
        
        return code
    
    def _get_default_value(self, field: str, problem_description: str, language: str) -> str:
        """기본값 생성"""
        defaults = {
            'title': f'{language.title()} Algorithm Solution',
            'code': self.language_templates[language]['example'],
            'explanation': f'Algorithm solution for: {problem_description[:100]}...',
            'time_complexity': 'O(n)',
            'space_complexity': 'O(1)'
        }
        return defaults.get(field, '')
    
    def _generate_fallback_solution(self, problem_description: str, language: str, difficulty: str) -> Dict[str, Any]:
        """AI 호출 실패 시 기본 솔루션 생성"""
        lang_info = self.language_templates.get(language.lower(), self.language_templates['python'])
        
        return {
            'title': f'{language.title()} Algorithm - {difficulty.title()}',
            'code': f'{lang_info["comment_style"]} Algorithm solution for: {problem_description[:50]}...\n{lang_info["example"]}',
            'explanation': f'This is a {difficulty} level algorithm solution. The problem requires: {problem_description}',
            'time_complexity': 'O(n)',
            'space_complexity': 'O(1)'
        }
    
    def validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """코드 유효성 검사 (기본적인 문법 체크)"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 기본적인 검사들
        if not code.strip():
            validation_result['is_valid'] = False
            validation_result['errors'].append('코드가 비어있습니다.')
        
        # 언어별 기본 검사
        if language.lower() == 'python':
            # Python 기본 문법 체크
            if 'def ' not in code and 'class ' not in code:
                validation_result['warnings'].append('함수나 클래스 정의가 없습니다.')
        
        return validation_result