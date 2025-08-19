import { render, screen } from '@testing-library/react';
import { Routes, Route, MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import Layout from './layouts/Layout';
import HomePage from './pages/HomePage';
import PhotoUploadPage from './pages/PhotoUploadPage';
import ConversationPage from './pages/ConversationPage';
import ReportsPage from './pages/ReportsPage';

describe('App Router', () => {
  it('renders home page by default', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { level: 1, name: '메멘토 박스' })).toBeInTheDocument();
    expect(screen.getByText('사진 업로드')).toBeInTheDocument();
    expect(screen.getByText('추억의 사진을 올려보세요')).toBeInTheDocument();
  });

  it('renders photo upload page when navigating to /photos', () => {
    render(
      <MemoryRouter initialEntries={['/photos']}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route path="photos" element={<PhotoUploadPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { level: 1, name: '사진 업로드' })).toBeInTheDocument();
    expect(screen.getByText('추억의 사진을 업로드하여 회상 대화를 시작해보세요.')).toBeInTheDocument();
  });

  it('renders conversation page when navigating to /conversation', () => {
    render(
      <MemoryRouter initialEntries={['/conversation']}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route path="conversation" element={<ConversationPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { level: 1, name: '회상 대화' })).toBeInTheDocument();
    expect(screen.getByText('사진을 보며 추억을 나누고 자연스러운 대화를 나눠보세요.')).toBeInTheDocument();
  });

  it('renders reports page when navigating to /reports', () => {
    render(
      <MemoryRouter initialEntries={['/reports']}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route path="reports" element={<ReportsPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { level: 1, name: '인지 리포트' })).toBeInTheDocument();
    expect(screen.getByText('대화 세션의 결과와 인지 기능 평가 결과를 확인하세요.')).toBeInTheDocument();
  });
});