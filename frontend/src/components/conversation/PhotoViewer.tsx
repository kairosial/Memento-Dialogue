import { useState, memo } from 'react';
import { PhotoContext } from '../../types/conversation';
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCw, Eye, EyeOff } from 'lucide-react';

interface PhotoViewerProps {
  photos: PhotoContext[];
  currentPhotoIndex: number;
  onPhotoChange: (index: number) => void;
  onClose?: () => void;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
  className?: string;
}

export const PhotoViewer = memo(({ 
  photos, 
  currentPhotoIndex, 
  onPhotoChange, 
  onClose,
  isMinimized = false,
  onToggleMinimize,
  className = ""
}: PhotoViewerProps) => {
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  
  const currentPhoto = photos[currentPhotoIndex];
  
  if (!currentPhoto) {
    return null;
  }

  const handlePrevious = () => {
    if (currentPhotoIndex > 0) {
      onPhotoChange(currentPhotoIndex - 1);
      setZoom(1);
      setRotation(0);
    }
  };

  const handleNext = () => {
    if (currentPhotoIndex < photos.length - 1) {
      onPhotoChange(currentPhotoIndex + 1);
      setZoom(1);
      setRotation(0);
    }
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.25, 0.5));
  };

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const handleReset = () => {
    setZoom(1);
    setRotation(0);
  };

  // 최소화된 상태
  if (isMinimized) {
    return (
      <div className={`bg-white border-2 border-gray-200 rounded-xl shadow-lg ${className}`}>
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img
              src={currentPhoto.url}
              alt={currentPhoto.name}
              className="w-12 h-12 object-cover rounded-lg"
            />
            <div>
              <h4 className="font-medium text-gray-800 truncate max-w-32">
                {currentPhoto.name}
              </h4>
              <p className="text-sm text-gray-500">
                {currentPhotoIndex + 1} / {photos.length}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {onToggleMinimize && (
              <button
                onClick={onToggleMinimize}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                aria-label="사진 크게 보기"
              >
                <Eye className="w-5 h-5" />
              </button>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                aria-label="사진 닫기"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border-2 border-gray-200 rounded-xl shadow-lg ${className}`}>
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-800">{currentPhoto.name}</h3>
          <p className="text-sm text-gray-500">
            {currentPhotoIndex + 1} / {photos.length}개 사진
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {onToggleMinimize && (
            <button
              onClick={onToggleMinimize}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
              aria-label="사진 최소화"
            >
              <EyeOff className="w-5 h-5" />
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg"
              aria-label="사진 닫기"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* 사진 영역 */}
      <div className="relative bg-gray-50 overflow-hidden" style={{ height: '400px' }}>
        <img
          src={currentPhoto.url}
          alt={currentPhoto.description || currentPhoto.name}
          className="w-full h-full object-contain transition-transform duration-200"
          style={{
            transform: `scale(${zoom}) rotate(${rotation}deg)`,
            transformOrigin: 'center'
          }}
          draggable={false}
        />

        {/* 이전/다음 버튼 */}
        {photos.length > 1 && (
          <>
            <button
              onClick={handlePrevious}
              disabled={currentPhotoIndex === 0}
              className="absolute left-4 top-1/2 transform -translate-y-1/2 w-12 h-12 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="이전 사진"
            >
              <ChevronLeft className="w-6 h-6 text-gray-700" />
            </button>
            
            <button
              onClick={handleNext}
              disabled={currentPhotoIndex === photos.length - 1}
              className="absolute right-4 top-1/2 transform -translate-y-1/2 w-12 h-12 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="다음 사진"
            >
              <ChevronRight className="w-6 h-6 text-gray-700" />
            </button>
          </>
        )}
      </div>

      {/* 컨트롤 바 */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          {/* 줌/회전 컨트롤 */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleZoomOut}
              disabled={zoom <= 0.5}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="축소"
            >
              <ZoomOut className="w-5 h-5" />
            </button>
            
            <span className="text-sm text-gray-600 font-mono min-w-12 text-center">
              {Math.round(zoom * 100)}%
            </span>
            
            <button
              onClick={handleZoomIn}
              disabled={zoom >= 3}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="확대"
            >
              <ZoomIn className="w-5 h-5" />
            </button>
            
            <div className="w-px h-6 bg-gray-300 mx-2" />
            
            <button
              onClick={handleRotate}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
              aria-label="회전"
            >
              <RotateCw className="w-5 h-5" />
            </button>
          </div>

          {/* 리셋 버튼 */}
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg"
          >
            원본 크기
          </button>
        </div>

        {/* 사진 설명 */}
        {currentPhoto.description && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-700 leading-relaxed">
              {currentPhoto.description}
            </p>
          </div>
        )}

        {/* 사진 태그 */}
        {currentPhoto.tags && currentPhoto.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {currentPhoto.tags.map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

PhotoViewer.displayName = 'PhotoViewer';