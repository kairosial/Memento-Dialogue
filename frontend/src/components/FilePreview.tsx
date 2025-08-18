import { useState, useEffect } from 'react';

interface FilePreviewProps {
  files: File[];
  onRemoveFile?: (index: number) => void;
  className?: string;
}

interface FilePreviewItem {
  file: File;
  previewUrl: string;
}

export default function FilePreview({ files, onRemoveFile, className = '' }: FilePreviewProps) {
  const [previews, setPreviews] = useState<FilePreviewItem[]>([]);

  useEffect(() => {
    const newPreviews: FilePreviewItem[] = [];

    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          newPreviews.push({
            file,
            previewUrl: e.target.result as string
          });
          
          // Update state when all previews are loaded
          if (newPreviews.length === files.length) {
            setPreviews([...newPreviews]);
          }
        }
      };
      reader.readAsDataURL(file);
    });

    // Cleanup function to revoke object URLs
    return () => {
      newPreviews.forEach(preview => {
        if (preview.previewUrl.startsWith('blob:')) {
          URL.revokeObjectURL(preview.previewUrl);
        }
      });
    };
  }, [files]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (files.length === 0) return null;

  return (
    <div className={`file-preview ${className}`}>
      <h3>선택된 파일 ({files.length}개)</h3>
      <div className="preview-grid">
        {previews.map((preview, index) => (
          <div key={index} className="preview-item">
            <div className="preview-image-container">
              <img 
                src={preview.previewUrl} 
                alt={preview.file.name}
                className="preview-image"
              />
              {onRemoveFile && (
                <button
                  className="remove-button"
                  onClick={() => onRemoveFile(index)}
                  type="button"
                  aria-label="파일 제거"
                >
                  <svg 
                    width="16" 
                    height="16" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M6 18L18 6M6 6l12 12" 
                    />
                  </svg>
                </button>
              )}
            </div>
            <div className="preview-info">
              <p className="file-name" title={preview.file.name}>
                {preview.file.name}
              </p>
              <p className="file-size">
                {formatFileSize(preview.file.size)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}