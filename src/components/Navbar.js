import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Menu, X, Code, Trophy, User, LogOut, Plus } from 'lucide-react';

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
    setIsMenuOpen(false);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <nav className="bg-white shadow-lg border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2" onClick={closeMenu}>
            <Code className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-800">AI 코딩 튜터</span>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center space-x-6">
            <Link 
              to="/rankings" 
              className="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <Trophy className="h-4 w-4" />
              <span>랭킹</span>
            </Link>

            {isAuthenticated ? (
              <>
                <Link 
                  to="/dashboard" 
                  className="text-gray-600 hover:text-blue-600 transition-colors"
                >
                  대시보드
                </Link>
                <Link 
                  to="/generate" 
                  className="flex items-center space-x-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  <span>알고리즘 생성</span>
                </Link>
                <Link 
                  to="/my-algorithms" 
                  className="text-gray-600 hover:text-blue-600 transition-colors"
                >
                  내 알고리즘
                </Link>
                
                {/* User Menu */}
                <div className="relative group">
                  <button className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors">
                    <User className="h-4 w-4" />
                    <span>{user?.username}</span>
                  </button>
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                    <div className="py-2">
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>로그아웃</span>
                      </button>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-4">
                <Link 
                  to="/login" 
                  className="text-gray-600 hover:text-blue-600 transition-colors"
                >
                  로그인
                </Link>
                <Link 
                  to="/register" 
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  회원가입
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-gray-200 py-4">
            <div className="flex flex-col space-y-4">
              <Link 
                to="/rankings" 
                className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors"
                onClick={closeMenu}
              >
                <Trophy className="h-4 w-4" />
                <span>랭킹</span>
              </Link>

              {isAuthenticated ? (
                <>
                  <Link 
                    to="/dashboard" 
                    className="text-gray-600 hover:text-blue-600 transition-colors"
                    onClick={closeMenu}
                  >
                    대시보드
                  </Link>
                  <Link 
                    to="/generate" 
                    className="flex items-center space-x-2 text-blue-600"
                    onClick={closeMenu}
                  >
                    <Plus className="h-4 w-4" />
                    <span>알고리즘 생성</span>
                  </Link>
                  <Link 
                    to="/my-algorithms" 
                    className="text-gray-600 hover:text-blue-600 transition-colors"
                    onClick={closeMenu}
                  >
                    내 알고리즘
                  </Link>
                  <div className="border-t border-gray-200 pt-4">
                    <div className="flex items-center space-x-2 text-gray-600 mb-2">
                      <User className="h-4 w-4" />
                      <span>{user?.username}</span>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="flex items-center space-x-2 text-red-600 hover:text-red-700"
                    >
                      <LogOut className="h-4 w-4" />
                      <span>로그아웃</span>
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <Link 
                    to="/login" 
                    className="text-gray-600 hover:text-blue-600 transition-colors"
                    onClick={closeMenu}
                  >
                    로그인
                  </Link>
                  <Link 
                    to="/register" 
                    className="text-blue-600 hover:text-blue-700 transition-colors"
                    onClick={closeMenu}
                  >
                    회원가입
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;