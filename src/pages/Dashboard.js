import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { 
  BarChart3, 
  Code, 
  Trophy, 
  Plus, 
  TrendingUp, 
  Star,
  Clock,
  Database,
  User
} from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalAlgorithms: 0,
    averageRating: 0,
    totalRatings: 0,
    rankPosition: null
  });
  const [recentAlgorithms, setRecentAlgorithms] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // 내 알고리즘 가져오기
      const algorithmsResponse = await axios.get('/api/my-algorithms');
      const algorithms = algorithmsResponse.data.algorithms;
      
      // 통계 계산
      const totalAlgorithms = algorithms.length;
      const totalRatings = algorithms.reduce((sum, algo) => sum + algo.rating_count, 0);
      const averageRating = totalRatings > 0 
        ? algorithms.reduce((sum, algo) => sum + (algo.average_rating * algo.rating_count), 0) / totalRatings
        : 0;
      
      setStats({
        totalAlgorithms,
        averageRating: Math.round(averageRating * 10) / 10,
        totalRatings,
        rankPosition: null
      });
      
      // 최근 알고리즘 (최대 5개)
      setRecentAlgorithms(algorithms.slice(0, 5));
      
    } catch (error) {
      console.error('Dashboard data fetch error:', error);
    } finally {
      setLoading(false);
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

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
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
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          안녕하세요, {user?.username}님! 👋
        </h1>
        <p className="text-gray-600">
          오늘도 멋진 알고리즘을 만들어보세요.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-full">
              <Code className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">생성한 알고리즘</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.totalAlgorithms}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-yellow-100 rounded-full">
              <Star className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">평균 평점</h3>
              <p className="text-2xl font-bold text-gray-900">
                {stats.averageRating > 0 ? `${stats.averageRating}/5.0` : '-'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-green-100 rounded-full">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">받은 평점 수</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.totalRatings}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-purple-100 rounded-full">
              <Trophy className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">랭킹</h3>
              <p className="text-2xl font-bold text-gray-900">
                {stats.rankPosition ? `${stats.rankPosition}위` : '-'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Recent Algorithms */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-blue-600" />
                  <span>최근 생성한 알고리즘</span>
                </h2>
                <Link 
                  to="/my-algorithms"
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  전체 보기 →
                </Link>
              </div>
            </div>

            <div className="p-6">
              {recentAlgorithms.length === 0 ? (
                <div className="text-center py-12">
                  <Code className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-500 mb-2">
                    아직 생성한 알고리즘이 없습니다
                  </h3>
                  <p className="text-gray-400 mb-4">
                    첫 번째 알고리즘을 생성해보세요!
                  </p>
                  <Link
                    to="/generate"
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
                  >
                    <Plus className="h-4 w-4" />
                    <span>알고리즘 생성</span>
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentAlgorithms.map((algorithm) => (
                    <div key={algorithm.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-gray-800">{algorithm.title}</h3>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLanguageColor(algorithm.language)}`}>
                            {algorithm.language.toUpperCase()}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(algorithm.difficulty)}`}>
                            {algorithm.difficulty === 'easy' ? '쉬움' : 
                             algorithm.difficulty === 'medium' ? '보통' : '어려움'}
                          </span>
                        </div>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {algorithm.description}
                      </p>
                      
                      <div className="flex items-center justify-between text-sm text-gray-500">
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center space-x-1">
                            <Star className="h-4 w-4 text-yellow-500" />
                            <span>{algorithm.average_rating > 0 ? algorithm.average_rating : '-'}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <User className="h-4 w-4" />
                            <span>{algorithm.rating_count}개 평점</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock className="h-4 w-4" />
                            <span>{new Date(algorithm.created_at).toLocaleDateString('ko-KR')}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          {/* Quick Actions Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">빠른 실행</h2>
            <div className="space-y-3">
              <Link
                to="/generate"
                className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Plus className="h-5 w-5" />
                <span>새 알고리즘 생성</span>
              </Link>
              
              <Link
                to="/my-algorithms"
                className="w-full bg-gray-100 text-gray-700 p-3 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2"
              >
                <Code className="h-5 w-5" />
                <span>내 알고리즘</span>
              </Link>
              
              <Link
                to="/rankings"
                className="w-full bg-gray-100 text-gray-700 p-3 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2"
              >
                <Trophy className="h-5 w-5" />
                <span>랭킹 보기</span>
              </Link>
            </div>
          </div>

          {/* Tips Card */}
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">💡 팁</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• 구체적인 문제 설명일수록 더 정확한 알고리즘을 생성할 수 있어요</li>
              <li>• 다양한 프로그래밍 언어로 같은 문제를 해결해보세요</li>
              <li>• 커뮤니티의 평점을 통해 알고리즘 품질을 개선하세요</li>
            </ul>
          </div>

          {/* Progress Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">진행 상황</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>알고리즘 생성</span>
                  <span>{stats.totalAlgorithms}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${Math.min((stats.totalAlgorithms / 10) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>평점 획득</span>
                  <span>{stats.totalRatings}/50</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${Math.min((stats.totalRatings / 50) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;