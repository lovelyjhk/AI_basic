import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { 
  Code, 
  Star, 
  Clock, 
  Database, 
  User, 
  Copy,
  ArrowLeft,
  MessageCircle,
  Send
} from 'lucide-react';

const AlgorithmDetail = () => {
  const { id } = useParams();
  const { user, isAuthenticated } = useAuth();
  const [algorithm, setAlgorithm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [submittingRating, setSubmittingRating] = useState(false);

  useEffect(() => {
    fetchAlgorithm();
  }, [id]);

  const fetchAlgorithm = async () => {
    try {
      setLoading(true);
      // 실제 API에서는 단일 알고리즘을 가져오는 엔드포인트가 필요합니다
      // 여기서는 모든 알고리즘을 가져온 후 필터링합니다
      const response = await axios.get('/api/algorithms');
      const foundAlgorithm = response.data.algorithms.find(algo => algo.id === parseInt(id));
      
      if (foundAlgorithm) {
        setAlgorithm(foundAlgorithm);
      } else {
        setError('알고리즘을 찾을 수 없습니다.');
      }
    } catch (error) {
      setError('알고리즘을 불러오는데 실패했습니다.');
      console.error('Error fetching algorithm:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitRating = async () => {
    if (!isAuthenticated) {
      toast.error('로그인이 필요합니다.');
      return;
    }

    if (rating === 0) {
      toast.error('평점을 선택해주세요.');
      return;
    }

    try {
      setSubmittingRating(true);
      await axios.post(`/api/algorithms/${id}/rate`, {
        rating,
        comment
      });
      
      toast.success('평점이 등록되었습니다!');
      setRating(0);
      setComment('');
      
      // 알고리즘 정보 새로고침
      fetchAlgorithm();
    } catch (error) {
      const message = error.response?.data?.error || '평점 등록에 실패했습니다.';
      toast.error(message);
    } finally {
      setSubmittingRating(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(algorithm.code);
    toast.success('코드가 클립보드에 복사되었습니다!');
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !algorithm) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <Link
          to="/rankings"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          랭킹으로 돌아가기
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back Button */}
      <div className="mb-6">
        <Link
          to="/rankings"
          className="inline-flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>랭킹으로 돌아가기</span>
        </Link>
      </div>

      {/* Algorithm Header */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-800">{algorithm.title}</h1>
          <div className="flex items-center space-x-3">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getLanguageColor(algorithm.language)}`}>
              {algorithm.language.toUpperCase()}
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(algorithm.difficulty)}`}>
              {algorithm.difficulty === 'easy' ? '쉬움' : 
               algorithm.difficulty === 'medium' ? '보통' : '어려움'}
            </span>
          </div>
        </div>

        <p className="text-gray-600 mb-6 text-lg">{algorithm.description}</p>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-6 text-center">
          <div className="bg-gray-50 p-4 rounded-lg">
            <User className="h-6 w-6 text-gray-600 mx-auto mb-2" />
            <div className="text-sm text-gray-500">작성자</div>
            <div className="font-semibold">{algorithm.author}</div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <Star className="h-6 w-6 text-yellow-500 mx-auto mb-2" />
            <div className="text-sm text-gray-500">평점</div>
            <div className="font-semibold">{algorithm.average_rating}/5.0</div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <MessageCircle className="h-6 w-6 text-blue-600 mx-auto mb-2" />
            <div className="text-sm text-gray-500">평점 수</div>
            <div className="font-semibold">{algorithm.rating_count}</div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <Clock className="h-6 w-6 text-orange-600 mx-auto mb-2" />
            <div className="text-sm text-gray-500">시간 복잡도</div>
            <div className="font-semibold font-mono">{algorithm.time_complexity}</div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <Database className="h-6 w-6 text-purple-600 mx-auto mb-2" />
            <div className="text-sm text-gray-500">공간 복잡도</div>
            <div className="font-semibold font-mono">{algorithm.space_complexity}</div>
          </div>
        </div>
      </div>

      {/* Code Section */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center space-x-2">
            <Code className="h-6 w-6 text-blue-600" />
            <span>코드</span>
          </h2>
          <button
            onClick={copyToClipboard}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Copy className="h-4 w-4" />
            <span>복사</span>
          </button>
        </div>

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

      {/* Explanation Section */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">알고리즘 설명</h2>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-line leading-relaxed">
            {algorithm.explanation}
          </p>
        </div>
      </div>

      {/* Rating Section */}
      {isAuthenticated && (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">이 알고리즘을 평가해주세요</h2>
          
          {/* Star Rating */}
          <div className="mb-6">
            <div className="text-sm text-gray-600 mb-2">평점</div>
            <div className="flex items-center space-x-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => setRating(star)}
                  className={`h-8 w-8 ${
                    star <= rating ? 'text-yellow-500' : 'text-gray-300'
                  } hover:text-yellow-400 transition-colors`}
                >
                  <Star className="h-8 w-8 fill-current" />
                </button>
              ))}
              <span className="ml-2 text-gray-600">
                {rating > 0 && `${rating}/5`}
              </span>
            </div>
          </div>

          {/* Comment */}
          <div className="mb-6">
            <label className="block text-sm text-gray-600 mb-2">
              코멘트 (선택사항)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="4"
              placeholder="이 알고리즘에 대한 의견을 남겨주세요..."
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={submitRating}
            disabled={submittingRating || rating === 0}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {submittingRating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>등록 중...</span>
              </>
            ) : (
              <>
                <Send className="h-5 w-5" />
                <span>평점 등록</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Login Prompt for Non-authenticated Users */}
      {!isAuthenticated && (
        <div className="bg-blue-50 rounded-lg p-8 text-center">
          <h3 className="text-lg font-semibold text-blue-800 mb-2">
            이 알고리즘을 평가해보세요!
          </h3>
          <p className="text-blue-600 mb-4">
            로그인하시면 평점을 남기고 커뮤니티에 기여할 수 있습니다.
          </p>
          <Link
            to="/login"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-block"
          >
            로그인하기
          </Link>
        </div>
      )}
    </div>
  );
};

export default AlgorithmDetail;