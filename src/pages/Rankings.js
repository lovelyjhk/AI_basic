import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Trophy, Star, Clock, User, Code, Medal } from 'lucide-react';

const Rankings = () => {
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRankings();
  }, []);

  const fetchRankings = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/rankings');
      setRankings(response.data.rankings);
    } catch (error) {
      setError('랭킹 데이터를 불러오는데 실패했습니다.');
      console.error('Error fetching rankings:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Medal className="h-6 w-6 text-yellow-500" />;
    if (rank === 2) return <Medal className="h-6 w-6 text-gray-400" />;
    if (rank === 3) return <Medal className="h-6 w-6 text-amber-600" />;
    return <span className="text-lg font-bold text-gray-600">{rank}</span>;
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={fetchRankings}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center space-x-3 mb-4">
          <Trophy className="h-10 w-10 text-yellow-500" />
          <h1 className="text-4xl font-bold text-gray-800">알고리즘 랭킹</h1>
        </div>
        <p className="text-gray-600 text-lg">
          커뮤니티에서 가장 높은 평점을 받은 알고리즘들을 만나보세요
        </p>
      </div>

      {/* Rankings */}
      {rankings.length === 0 ? (
        <div className="text-center py-12">
          <Trophy className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-500 mb-2">
            아직 랭킹에 등록된 알고리즘이 없습니다
          </h3>
          <p className="text-gray-400 mb-4">
            첫 번째 알고리즘을 생성하고 평점을 받아보세요!
          </p>
          <Link
            to="/generate"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
          >
            <Code className="h-5 w-5" />
            <span>알고리즘 생성하기</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {rankings.map((algorithm, index) => (
            <div
              key={algorithm.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
            >
              <div className="flex items-center space-x-4">
                {/* Rank */}
                <div className="flex items-center justify-center w-12 h-12 bg-gray-50 rounded-full">
                  {getRankIcon(algorithm.rank)}
                </div>

                {/* Algorithm Info */}
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <Link
                      to={`/algorithm/${algorithm.id}`}
                      className="text-xl font-semibold text-gray-800 hover:text-blue-600 transition-colors"
                    >
                      {algorithm.title}
                    </Link>
                    
                    {/* Language Badge */}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLanguageColor(algorithm.language)}`}>
                      {algorithm.language.toUpperCase()}
                    </span>
                    
                    {/* Difficulty Badge */}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(algorithm.difficulty)}`}>
                      {algorithm.difficulty === 'easy' ? '쉬움' : 
                       algorithm.difficulty === 'medium' ? '보통' : '어려움'}
                    </span>
                  </div>

                  <div className="flex items-center space-x-6 text-sm text-gray-600">
                    {/* Author */}
                    <div className="flex items-center space-x-1">
                      <User className="h-4 w-4" />
                      <span>{algorithm.author}</span>
                    </div>

                    {/* Rating */}
                    <div className="flex items-center space-x-1">
                      <Star className="h-4 w-4 text-yellow-500 fill-current" />
                      <span className="font-medium">{algorithm.average_rating}</span>
                      <span className="text-gray-400">({algorithm.rating_count}개 평점)</span>
                    </div>

                    {/* Created Date */}
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4" />
                      <span>{new Date(algorithm.created_at).toLocaleDateString('ko-KR')}</span>
                    </div>
                  </div>
                </div>

                {/* Rating Score */}
                <div className="text-right">
                  <div className="text-3xl font-bold text-blue-600">
                    {algorithm.average_rating}
                  </div>
                  <div className="text-sm text-gray-500">
                    / 5.0
                  </div>
                </div>
              </div>

              {/* Top 3 Special Styling */}
              {algorithm.rank <= 3 && (
                <div className={`mt-4 p-3 rounded-lg ${
                  algorithm.rank === 1 ? 'bg-gradient-to-r from-yellow-50 to-yellow-100 border border-yellow-200' :
                  algorithm.rank === 2 ? 'bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200' :
                  'bg-gradient-to-r from-amber-50 to-amber-100 border border-amber-200'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {algorithm.rank === 1 && (
                        <>
                          <Trophy className="h-5 w-5 text-yellow-600" />
                          <span className="text-yellow-800 font-medium">🏆 1위 알고리즘</span>
                        </>
                      )}
                      {algorithm.rank === 2 && (
                        <>
                          <Medal className="h-5 w-5 text-gray-600" />
                          <span className="text-gray-800 font-medium">🥈 2위 알고리즘</span>
                        </>
                      )}
                      {algorithm.rank === 3 && (
                        <>
                          <Medal className="h-5 w-5 text-amber-600" />
                          <span className="text-amber-800 font-medium">🥉 3위 알고리즘</span>
                        </>
                      )}
                    </div>
                    <Link
                      to={`/algorithm/${algorithm.id}`}
                      className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                    >
                      자세히 보기 →
                    </Link>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Call to Action */}
      {rankings.length > 0 && (
        <div className="mt-12 text-center bg-blue-50 rounded-lg p-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-4">
            당신의 알고리즘도 랭킹에 도전해보세요!
          </h3>
          <p className="text-gray-600 mb-6">
            AI의 도움으로 최적화된 알고리즘을 생성하고 커뮤니티의 평가를 받아보세요.
          </p>
          <Link
            to="/generate"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
          >
            <Code className="h-5 w-5" />
            <span>알고리즘 생성하기</span>
          </Link>
        </div>
      )}
    </div>
  );
};

export default Rankings;