import { useState, useRef, type DragEvent, type ChangeEvent } from 'react';

interface FileDropZoneProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  maxFiles?: number;
  disabled?: boolean;
  className?: string;
}

export default function FileDropZone({
  onFilesSelected,
  accept = 'image/jpeg,image/jpg,image/png,image/webp',
  multiple = true,
  maxFiles = 10,
  disabled = false,
  className = ''
}: FileDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(file => {
      const acceptedTypes = accept.split(',').map(type => type.trim());
      return acceptedTypes.includes(file.type);
    });

    if (validFiles.length > maxFiles) {
      alert(`최대 ${maxFiles}개의 파일만 선택할 수 있습니다.`);
      return;
    }

    if (validFiles.length > 0) {
      onFilesSelected(validFiles);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    if (files.length > maxFiles) {
      alert(`최대 ${maxFiles}개의 파일만 선택할 수 있습니다.`);
      return;
    }

    if (files.length > 0) {
      onFilesSelected(files);
    }
    
    // Reset input value to allow selecting the same files again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div
      className={`file-drop-zone ${className} ${isDragOver ? 'drag-over' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
        disabled={disabled}
      />
      
      <div className="drop-zone-content">
        <svg 
          className="upload-icon" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
          width="48" 
          height="48"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
          />
        </svg>
        
        <div className="drop-zone-text">
          <p className="drop-zone-title">
            {isDragOver ? '파일을 여기에 놓으세요' : '사진을 업로드하세요'}
          </p>
          <p className="drop-zone-subtitle">
            클릭하거나 파일을 드래그해서 업로드
          </p>
          <p className="drop-zone-info">
            JPEG, PNG, WebP 형식 지원 (최대 {maxFiles}개, 10MB 이하)
          </p>
        </div>
      </div>
    </div>
  );
}