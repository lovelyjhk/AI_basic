import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Code, Zap, Trophy, Users, ArrowRight, Star } from 'lucide-react';

const Home = () => {
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: <Code className="h-8 w-8 text-blue-600" />,
      title: "다중 언어 지원",
      description: "Python, JavaScript, Java, C++, C, Go, Rust, V-lang 등 8개 언어 지원"
    },
    {
      icon: <Zap className="h-8 w-8 text-yellow-600" />,
      title: "AI 기반 생성",
      description: "최신 GPT-4 모델을 활용한 고품질 알고리즘 자동 생성"
    },
    {
      icon: <Trophy className="h-8 w-8 text-green-600" />,
      title: "랭킹 시스템",
      description: "커뮤니티 평점을 통한 알고리즘 품질 검증 및 랭킹"
    },
    {
      icon: <Users className="h-8 w-8 text-purple-600" />,
      title: "커뮤니티",
      description: "다른 개발자들과 알고리즘을 공유하고 피드백 교환"
    }
  ];

  const languages = [
    { name: "Python", color: "bg-blue-500" },
    { name: "JavaScript", color: "bg-yellow-500" },
    { name: "Java", color: "bg-red-500" },
    { name: "C++", color: "bg-purple-500" },
    { name: "C", color: "bg-gray-600" },
    { name: "Go", color: "bg-cyan-500" },
    { name: "Rust", color: "bg-orange-500" },
    { name: "V-lang", color: "bg-green-500" }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            AI 코딩 튜터
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-blue-100">
            인공지능이 만들어주는 맞춤형 알고리즘 솔루션
          </p>
          <p className="text-lg mb-10 text-blue-200 max-w-2xl mx-auto">
            문제를 설명하면 AI가 8개 언어로 최적화된 알고리즘을 생성해드립니다. 
            커뮤니티 평점으로 검증된 고품질 솔루션을 만나보세요.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            {isAuthenticated ? (
              <Link
                to="/generate"
                className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 transition-colors flex items-center space-x-2"
              >
                <span>알고리즘 생성하기</span>
                <ArrowRight className="h-5 w-5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 transition-colors flex items-center space-x-2"
                >
                  <span>무료로 시작하기</span>
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  to="/rankings"
                  className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors"
                >
                  랭킹 둘러보기
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Language Support */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-800">
            지원하는 프로그래밍 언어
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {languages.map((lang, index) => (
              <div key={index} className="bg-white rounded-lg p-4 shadow-md hover:shadow-lg transition-shadow">
                <div className={`w-4 h-4 ${lang.color} rounded-full mb-2`}></div>
                <h3 className="font-semibold text-gray-800">{lang.name}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-800">
            주요 기능
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
                <div className="mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-3 text-gray-800">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-800">
            사용 방법
          </h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="bg-blue-600 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                1
              </div>
              <h3 className="text-xl font-semibold mb-3">문제 설명</h3>
              <p className="text-gray-600">
                해결하고 싶은 알고리즘 문제를 자연어로 설명합니다
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-600 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                2
              </div>
              <h3 className="text-xl font-semibold mb-3">AI 생성</h3>
              <p className="text-gray-600">
                AI가 선택한 언어와 난이도에 맞는 최적의 솔루션을 생성합니다
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-600 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                3
              </div>
              <h3 className="text-xl font-semibold mb-3">공유 & 평가</h3>
              <p className="text-gray-600">
                생성된 알고리즘을 커뮤니티에 공유하고 평점을 받습니다
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonial */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="bg-blue-600 rounded-2xl p-8 text-white text-center max-w-4xl mx-auto">
            <div className="flex justify-center mb-4">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="h-6 w-6 text-yellow-400 fill-current" />
              ))}
            </div>
            <blockquote className="text-xl md:text-2xl mb-6">
              "AI 코딩 튜터 덕분에 복잡한 알고리즘 문제를 빠르게 해결할 수 있게 되었습니다. 
              다양한 언어로 최적화된 솔루션을 제공받을 수 있어서 정말 유용해요!"
            </blockquote>
            <cite className="text-blue-200">- 김개발, 소프트웨어 엔지니어</cite>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gray-900 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6">
            지금 시작해보세요
          </h2>
          <p className="text-xl mb-8 text-gray-300">
            AI의 힘으로 더 나은 개발자가 되어보세요
          </p>
          {!isAuthenticated && (
            <Link
              to="/register"
              className="bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
            >
              <span>무료 회원가입</span>
              <ArrowRight className="h-5 w-5" />
            </Link>
          )}
        </div>
      </section>
    </div>
  );
};

export default Home;