import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  Code, 
  Star, 
  Clock, 
  Database, 
  User, 
  Plus,
  Eye,
  Copy,
  Filter,
  Search
} from 'lucide-react';
import toast from 'react-hot-toast';

const MyAlgorithms = () => {
  const [algorithms, setAlgorithms] = useState([]);
  const [filteredAlgorithms, setFilteredAlgorithms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [languageFilter, setLanguageFilter] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [expandedAlgorithm, setExpandedAlgorithm] = useState(null);

  const languages = ['python', 'javascript', 'java', 'cpp', 'c', 'go', 'rust', 'vlang'];
  const difficulties = ['easy', 'medium', 'hard'];

  useEffect(() => {
    fetchMyAlgorithms();
  }, []);

  useEffect(() => {
    filterAlgorithms();
  }, [algorithms, searchTerm, languageFilter, difficultyFilter]);

  const fetchMyAlgorithms = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/my-algorithms');
      setAlgorithms(response.data.algorithms);
    } catch (error) {
      console.error('Error fetching algorithms:', error);
      toast.error('알고리즘을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const filterAlgorithms = () => {
    let filtered = algorithms;

    if (searchTerm) {
      filtered = filtered.filter(algo =>
        algo.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        algo.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (languageFilter) {
      filtered = filtered.filter(algo => algo.language === languageFilter);
    }

    if (difficultyFilter) {
      filtered = filtered.filter(algo => algo.difficulty === difficultyFilter);
    }

    setFilteredAlgorithms(filtered);
  };

  const getLanguageColor = (language) => {
    const colors = {
      python: 'bg-blue-100 text-blue-800',
      javascript: 'bg-yellow-100 text-yellow-800',
      java: 'bg-red-100 text-red-800',
      cpp: 'bg-purple-100 text-purple-800',
      c: 'bg-gray-100 text-gray-800',
      go: 'bg-cyan-100 text-cyan-800',
      rust: 'bg-orange-100 text-orange-800',
      vlang: 'bg-green-100 text-green-800'
    };
    return colors[language] || 'bg-gray-100 text-gray-800';
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSyntaxLanguage = (language) => {
    const mapping = {
      cpp: 'cpp',
      vlang: 'v'
    };
    return mapping[language] || language;
  };

  const copyToClipboard = (code) => {
    navigator.clipboard.writeText(code);
    toast.success('코드가 클립보드에 복사되었습니다!');
  };

  const toggleExpanded = (algorithmId) => {
    setExpandedAlgorithm(expandedAlgorithm === algorithmId ? null : algorithmId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">내 알고리즘</h1>
          <p className="text-gray-600">
            생성한 알고리즘 {algorithms.length}개를 관리하고 확인하세요
          </p>
        </div>
        <Link
          to="/generate"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <Plus className="h-5 w-5" />
          <span>새 알고리즘 생성</span>
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="제목이나 설명으로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Language Filter */}
          <div>
            <select
              value={languageFilter}
              onChange={(e) => setLanguageFilter(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">모든 언어</option>
              {languages.map(lang => (
                <option key={lang} value={lang}>
                  {lang.charAt(0).toUpperCase() + lang.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Difficulty Filter */}
          <div>
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">모든 난이도</option>
              <option value="easy">쉬움</option>
              <option value="medium">보통</option>
              <option value="hard">어려움</option>
            </select>
          </div>
        </div>
      </div>

      {/* Algorithms List */}
      {filteredAlgorithms.length === 0 ? (
        <div className="text-center py-12">
          <Code className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-500 mb-2">
            {algorithms.length === 0 ? '생성한 알고리즘이 없습니다' : '검색 결과가 없습니다'}
          </h3>
          <p className="text-gray-400 mb-4">
            {algorithms.length === 0 
              ? '첫 번째 알고리즘을 생성해보세요!'
              : '다른 검색 조건을 시도해보세요.'
            }
          </p>
          {algorithms.length === 0 && (
            <Link
              to="/generate"
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>알고리즘 생성</span>
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {filteredAlgorithms.map((algorithm) => (
            <div key={algorithm.id} className="bg-white rounded-lg shadow-md overflow-hidden">
              {/* Algorithm Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-800">{algorithm.title}</h2>
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getLanguageColor(algorithm.language)}`}>
                      {algorithm.language.toUpperCase()}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(algorithm.difficulty)}`}>
                      {algorithm.difficulty === 'easy' ? '쉬움' : 
                       algorithm.difficulty === 'medium' ? '보통' : '어려움'}
                    </span>
                  </div>
                </div>

                <p className="text-gray-600 mb-4">{algorithm.description}</p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-6 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Star className="h-4 w-4 text-yellow-500" />
                      <span>{algorithm.average_rating > 0 ? algorithm.average_rating : '-'}/5.0</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <User className="h-4 w-4" />
                      <span>{algorithm.rating_count}개 평점</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4" />
                      <span>{new Date(algorithm.created_at).toLocaleDateString('ko-KR')}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4 text-orange-600" />
                      <span>{algorithm.time_complexity}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Database className="h-4 w-4 text-purple-600" />
                      <span>{algorithm.space_complexity}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => copyToClipboard(algorithm.code)}
                      className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
                      title="코드 복사"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => toggleExpanded(algorithm.id)}
                      className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
                      title={expandedAlgorithm === algorithm.id ? "접기" : "상세 보기"}
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {expandedAlgorithm === algorithm.id && (
                <div className="p-6 bg-gray-50">
                  {/* Code */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3">코드</h3>
                    <div className="relative">
                      <SyntaxHighlighter
                        language={getSyntaxLanguage(algorithm.language)}
                        style={vscDarkPlus}
                        className="rounded-lg"
                      >
                        {algorithm.code}
                      </SyntaxHighlighter>
                    </div>
                  </div>

                  {/* Explanation */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">알고리즘 설명</h3>
                    <div className="bg-white p-4 rounded-lg">
                      <p className="text-gray-700 whitespace-pre-line">
                        {algorithm.explanation}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyAlgorithms;