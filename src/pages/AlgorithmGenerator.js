import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Code, Zap, Clock, Database, Copy, Save } from 'lucide-react';

const AlgorithmGenerator = () => {
  const [formData, setFormData] = useState({
    problem_description: '',
    language: 'python',
    difficulty: 'medium'
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  const languages = [
    { value: 'python', label: 'Python', syntax: 'python' },
    { value: 'javascript', label: 'JavaScript', syntax: 'javascript' },
    { value: 'java', label: 'Java', syntax: 'java' },
    { value: 'cpp', label: 'C++', syntax: 'cpp' },
    { value: 'c', label: 'C', syntax: 'c' },
    { value: 'go', label: 'Go', syntax: 'go' },
    { value: 'rust', label: 'Rust', syntax: 'rust' },
    { value: 'vlang', label: 'V-lang', syntax: 'v' }
  ];

  const difficulties = [
    { value: 'easy', label: '쉬움', color: 'text-green-600' },
    { value: 'medium', label: '보통', color: 'text-yellow-600' },
    { value: 'hard', label: '어려움', color: 'text-red-600' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.problem_description.trim()) {
      toast.error('문제 설명을 입력해주세요.');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/generate-algorithm', formData);
      setResult(response.data.algorithm);
      toast.success('알고리즘이 성공적으로 생성되었습니다!');
    } catch (error) {
      const message = error.response?.data?.error || '알고리즘 생성에 실패했습니다.';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result.code);
    toast.success('코드가 클립보드에 복사되었습니다!');
  };

  const saveAlgorithm = () => {
    // 이미 저장된 상태이므로 내 알고리즘 페이지로 이동
    navigate('/my-algorithms');
    toast.success('알고리즘이 저장되었습니다!');
  };

  const selectedLanguage = languages.find(lang => lang.value === formData.language);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          AI 알고리즘 생성기
        </h1>
        <p className="text-gray-600">
          문제를 설명하면 AI가 최적화된 알고리즘 솔루션을 생성해드립니다.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Problem Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                문제 설명 *
              </label>
              <textarea
                name="problem_description"
                value={formData.problem_description}
                onChange={handleInputChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="6"
                placeholder="예: 두 수의 합이 특정 값과 같은 배열의 인덱스를 찾는 알고리즘을 만들어주세요."
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                구체적으로 설명할수록 더 정확한 알고리즘을 생성할 수 있습니다.
              </p>
            </div>

            {/* Language Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                프로그래밍 언어
              </label>
              <select
                name="language"
                value={formData.language}
                onChange={handleInputChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {languages.map(lang => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Difficulty Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                난이도
              </label>
              <div className="grid grid-cols-3 gap-2">
                {difficulties.map(diff => (
                  <label key={diff.value} className="cursor-pointer">
                    <input
                      type="radio"
                      name="difficulty"
                      value={diff.value}
                      checked={formData.difficulty === diff.value}
                      onChange={handleInputChange}
                      className="sr-only"
                    />
                    <div className={`p-3 border rounded-lg text-center transition-all ${
                      formData.difficulty === diff.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}>
                      <span className={diff.color}>{diff.label}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>생성 중...</span>
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5" />
                  <span>알고리즘 생성</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Result Display */}
        <div className="bg-white rounded-lg shadow-md p-6">
          {result ? (
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center space-x-2">
                  <Code className="h-6 w-6 text-blue-600" />
                  <span>{result.title}</span>
                </h2>
                <div className="flex space-x-2">
                  <button
                    onClick={copyToClipboard}
                    className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
                    title="코드 복사"
                  >
                    <Copy className="h-5 w-5" />
                  </button>
                  <button
                    onClick={saveAlgorithm}
                    className="p-2 text-gray-600 hover:text-green-600 transition-colors"
                    title="알고리즘 저장"
                  >
                    <Save className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* Code */}
              <div className="relative">
                <div className="bg-gray-800 text-white px-4 py-2 rounded-t-lg text-sm flex items-center justify-between">
                  <span>{selectedLanguage?.label}</span>
                  <span className="text-gray-400">
                    {formData.difficulty} 난이도
                  </span>
                </div>
                <SyntaxHighlighter
                  language={selectedLanguage?.syntax}
                  style={vscDarkPlus}
                  className="rounded-b-lg"
                  customStyle={{ margin: 0 }}
                >
                  {result.code}
                </SyntaxHighlighter>
              </div>

              {/* Complexity */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Clock className="h-5 w-5 text-orange-600" />
                    <span className="font-medium">시간 복잡도</span>
                  </div>
                  <span className="text-lg font-mono text-gray-800">
                    {result.time_complexity}
                  </span>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Database className="h-5 w-5 text-purple-600" />
                    <span className="font-medium">공간 복잡도</span>
                  </div>
                  <span className="text-lg font-mono text-gray-800">
                    {result.space_complexity}
                  </span>
                </div>
              </div>

              {/* Explanation */}
              <div>
                <h3 className="text-lg font-semibold mb-3">알고리즘 설명</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700 whitespace-pre-line">
                    {result.explanation}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-4">
                <button
                  onClick={() => navigate('/my-algorithms')}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
                >
                  내 알고리즘 보기
                </button>
                <button
                  onClick={() => {
                    setResult(null);
                    setFormData({
                      problem_description: '',
                      language: 'python',
                      difficulty: 'medium'
                    });
                  }}
                  className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  새로 생성하기
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <Code className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-500 mb-2">
                알고리즘을 생성해보세요
              </h3>
              <p className="text-gray-400">
                왼쪽 폼을 작성하고 '알고리즘 생성' 버튼을 클릭하세요.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlgorithmGenerator;