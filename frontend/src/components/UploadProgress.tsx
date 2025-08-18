
interface UploadProgressItem {
  fileName: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

interface UploadProgressProps {
  items: UploadProgressItem[];
  onClear?: () => void;
}

export default function UploadProgress({ items, onClear }: UploadProgressProps) {
  if (items.length === 0) return null;

  const completedCount = items.filter(item => item.status === 'completed').length;
  const errorCount = items.filter(item => item.status === 'error').length;
  const totalCount = items.length;

  return (
    <div className="upload-progress">
      <div className="upload-progress-header">
        <h3>업로드 진행 상황</h3>
        <div className="upload-progress-summary">
          {completedCount > 0 && (
            <span className="completed-count">완료: {completedCount}</span>
          )}
          {errorCount > 0 && (
            <span className="error-count">실패: {errorCount}</span>
          )}
          <span className="total-count">전체: {totalCount}</span>
        </div>
        {onClear && (completedCount === totalCount || errorCount > 0) && (
          <button 
            className="clear-button" 
            onClick={onClear}
            type="button"
          >
            닫기
          </button>
        )}
      </div>

      <div className="upload-progress-list">
        {items.map((item, index) => (
          <div key={index} className={`upload-progress-item ${item.status}`}>
            <div className="file-info">
              <span className="file-name">{item.fileName}</span>
              <span className="file-status">
                {item.status === 'pending' && '대기 중'}
                {item.status === 'uploading' && '업로드 중...'}
                {item.status === 'completed' && '완료'}
                {item.status === 'error' && '실패'}
              </span>
            </div>
            
            <div className="progress-container">
              <div 
                className="progress-bar"
                style={{ width: `${item.progress}%` }}
              />
            </div>
            
            {item.error && (
              <div className="error-message">
                {item.error}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}