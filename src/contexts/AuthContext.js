import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Axios 인터셉터 설정
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // 초기 사용자 정보 로드
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          // 토큰이 있으면 사용자 정보를 로드하는 로직
          // 여기서는 토큰만 있으면 로그인된 것으로 간주
          const userData = JSON.parse(localStorage.getItem('user') || '{}');
          if (userData.id) {
            setUser(userData);
          }
        } catch (error) {
          console.error('사용자 정보 로드 실패:', error);
          logout();
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await axios.post('/api/login', {
        username,
        password
      });

      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      toast.success('로그인 성공!');
      return true;
    } catch (error) {
      const message = error.response?.data?.error || '로그인에 실패했습니다.';
      toast.error(message);
      return false;
    }
  };

  const register = async (username, email, password) => {
    try {
      const response = await axios.post('/api/register', {
        username,
        email,
        password
      });

      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      toast.success('회원가입이 완료되었습니다!');
      return true;
    } catch (error) {
      const message = error.response?.data?.error || '회원가입에 실패했습니다.';
      toast.error(message);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    toast.success('로그아웃되었습니다.');
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!token
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};