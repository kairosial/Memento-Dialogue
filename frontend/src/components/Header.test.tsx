import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import Header from './Header';

describe('Header Component', () => {
  it('renders navigation links', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );
    
    expect(screen.getByText('메멘토 박스')).toBeInTheDocument();
    expect(screen.getByText('사진')).toBeInTheDocument();
    expect(screen.getByText('대화')).toBeInTheDocument();
    expect(screen.getByText('리포트')).toBeInTheDocument();
  });

  it('highlights active navigation link', () => {
    render(
      <MemoryRouter initialEntries={['/photos']}>
        <Header />
      </MemoryRouter>
    );
    
    const photosLink = screen.getByText('사진');
    expect(photosLink).toHaveClass('active');
  });
});