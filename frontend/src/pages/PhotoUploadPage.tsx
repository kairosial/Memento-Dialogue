import { useState } from 'react';
import FileDropZone from '../components/FileDropZone';
import FilePreview from '../components/FilePreview';
import AlbumSelector from '../components/AlbumSelector';
import UploadProgress from '../components/UploadProgress';
import { useFileUpload } from '../hooks/useFileUpload';
import '../components/PhotoUpload.css';
import './PhotoUploadPage.css';

export default function PhotoUploadPage() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedAlbumId, setSelectedAlbumId] = useState<string | undefined>();
  const { uploadFiles, uploadProgress, isUploading, clearProgress } = useFileUpload();

  const handleFilesSelected = (files: File[]) => {
    setSelectedFiles(prev => [...prev, ...files]);
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      alert('업로드할 파일을 선택해주세요.');
      return;
    }

    try {
      await uploadFiles(selectedFiles, selectedAlbumId);
      setSelectedFiles([]);
    } catch (error) {
      console.error('업로드 실패:', error);
    }
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
    clearProgress();
  };

  return (
    <div className="page-container">
      <div className="photo-upload-page">
        <header className="page-header">
          <h1>사진 업로드</h1>
          <p>추억의 사진을 업로드하여 회상 대화를 시작해보세요.</p>
        </header>

        <div className="upload-section">
          <AlbumSelector
            selectedAlbumId={selectedAlbumId}
            onAlbumSelect={setSelectedAlbumId}
          />

          <FileDropZone
            onFilesSelected={handleFilesSelected}
            disabled={isUploading}
          />

          {selectedFiles.length > 0 && (
            <FilePreview
              files={selectedFiles}
              onRemoveFile={handleRemoveFile}
            />
          )}

          {uploadProgress.length > 0 && (
            <UploadProgress
              items={uploadProgress}
              onClear={clearProgress}
            />
          )}

          <div className="upload-actions">
            {selectedFiles.length > 0 && (
              <>
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="clear-all-button"
                  disabled={isUploading}
                >
                  모두 지우기
                </button>
                <button
                  type="button"
                  onClick={handleUpload}
                  className="upload-button"
                  disabled={isUploading || selectedFiles.length === 0}
                >
                  {isUploading ? '업로드 중...' : `업로드 시작 (${selectedFiles.length}개)`}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}