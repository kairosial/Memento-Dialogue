import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

interface Album {
  id: string;
  name: string;
  description?: string;
}

interface AlbumSelectorProps {
  selectedAlbumId?: string;
  onAlbumSelect: (albumId: string | undefined) => void;
  className?: string;
}

export default function AlbumSelector({ 
  selectedAlbumId, 
  onAlbumSelect, 
  className = '' 
}: AlbumSelectorProps) {
  const { user } = useAuth();
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAlbumName, setNewAlbumName] = useState('');
  const [newAlbumDescription, setNewAlbumDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadAlbums();
  }, [user]);

  const loadAlbums = async () => {
    if (!user?.id) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      
      // 개발 환경에서는 로컬 스토리지에서 앨범 로드
      if (import.meta.env.DEV && user.id === '00000000-0000-0000-0000-000000000001') {
        const localAlbums = JSON.parse(localStorage.getItem('dev_albums') || '[]');
        setAlbums(localAlbums.sort((a: Album, b: Album) => a.name.localeCompare(b.name)));
        setLoading(false);
        return;
      }

      const { data, error } = await supabase
        .from('albums')
        .select('*')
        .eq('user_id', user.id)
        .order('name');

      if (error) {
        console.error('앨범 로드 실패:', error);
      } else {
        setAlbums(data || []);
      }
    } catch (error) {
      console.error('앨범 로드 중 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const createAlbum = async () => {
    if (!newAlbumName.trim()) return;
    
    if (!user?.id) {
      alert('앨범을 생성하려면 로그인이 필요합니다.');
      return;
    }

    try {
      setCreating(true);
      
      // 개발 환경에서는 로컬 스토리지를 사용한 임시 앨범 생성
      if (import.meta.env.DEV && user.id === '00000000-0000-0000-0000-000000000001') {
        const newAlbum = {
          id: `local-album-${Date.now()}`,
          name: newAlbumName.trim(),
          description: newAlbumDescription.trim() || undefined,
          user_id: user.id,
          created_at: new Date().toISOString()
        };
        
        // 로컬 스토리지에 저장
        const existingAlbums = JSON.parse(localStorage.getItem('dev_albums') || '[]');
        const updatedAlbums = [...existingAlbums, newAlbum];
        localStorage.setItem('dev_albums', JSON.stringify(updatedAlbums));
        
        setAlbums(prev => [...prev, newAlbum]);
        setNewAlbumName('');
        setNewAlbumDescription('');
        setShowCreateForm(false);
        onAlbumSelect(newAlbum.id);
        return;
      }

      const { data, error } = await supabase
        .from('albums')
        .insert({
          name: newAlbumName.trim(),
          description: newAlbumDescription.trim() || undefined,
          user_id: user.id
        })
        .select()
        .single();

      if (error) {
        alert(`앨범 생성 실패: ${error.message}`);
      } else {
        setAlbums(prev => [...prev, data]);
        setNewAlbumName('');
        setNewAlbumDescription('');
        setShowCreateForm(false);
        onAlbumSelect(data.id);
      }
    } catch (error) {
      console.error('앨범 생성 중 오류:', error);
      alert('앨범 생성 중 오류가 발생했습니다.');
    } finally {
      setCreating(false);
    }
  };

  const handleCancelCreate = () => {
    setShowCreateForm(false);
    setNewAlbumName('');
    setNewAlbumDescription('');
  };

  return (
    <div className={`album-selector ${className}`}>
      <div className="album-selector-header">
        <label htmlFor="album-select">앨범 선택</label>
        <button
          type="button"
          onClick={() => setShowCreateForm(true)}
          className="create-album-button"
          disabled={showCreateForm}
        >
          + 새 앨범
        </button>
      </div>

      {loading ? (
        <div className="loading">앨범 목록을 불러오는 중...</div>
      ) : (
        <select
          id="album-select"
          value={selectedAlbumId || ''}
          onChange={(e) => onAlbumSelect(e.target.value || undefined)}
          className="album-select"
        >
          <option value="">앨범을 선택하세요</option>
          {albums.map(album => (
            <option key={album.id} value={album.id}>
              {album.name}
            </option>
          ))}
        </select>
      )}

      {showCreateForm && (
        <div className="create-album-form">
          <h4>새 앨범 만들기</h4>
          <div className="form-group">
            <label htmlFor="album-name">앨범 이름</label>
            <input
              id="album-name"
              type="text"
              value={newAlbumName}
              onChange={(e) => setNewAlbumName(e.target.value)}
              placeholder="앨범 이름을 입력하세요"
              maxLength={50}
            />
          </div>
          <div className="form-group">
            <label htmlFor="album-description">설명 (선택사항)</label>
            <textarea
              id="album-description"
              value={newAlbumDescription}
              onChange={(e) => setNewAlbumDescription(e.target.value)}
              placeholder="앨범에 대한 간단한 설명을 입력하세요"
              maxLength={200}
              rows={2}
            />
          </div>
          <div className="form-actions">
            <button
              type="button"
              onClick={createAlbum}
              disabled={!newAlbumName.trim() || creating}
              className="create-button"
            >
              {creating ? '생성 중...' : '생성'}
            </button>
            <button
              type="button"
              onClick={handleCancelCreate}
              disabled={creating}
              className="cancel-button"
            >
              취소
            </button>
          </div>
        </div>
      )}
    </div>
  );
}