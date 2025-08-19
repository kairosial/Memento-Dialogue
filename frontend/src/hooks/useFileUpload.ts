import { useState, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

interface UseFileUploadResult {
  uploadFiles: (files: File[], albumId?: string) => Promise<void>;
  uploadProgress: UploadProgress[];
  isUploading: boolean;
  clearProgress: () => void;
}

export function useFileUpload(): UseFileUploadResult {
  const { user } = useAuth();
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const validateFile = (file: File): string | null => {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return '지원되지 않는 파일 형식입니다. (JPEG, PNG, WebP만 가능)';
    }

    if (file.size > maxSize) {
      return '파일 크기가 너무 큽니다. (최대 10MB)';
    }

    return null;
  };

  const uploadFiles = useCallback(async (files: File[], albumId?: string) => {
    if (!user?.id) {
      throw new Error('파일을 업로드하려면 로그인이 필요합니다.');
    }

    const uploadSingleFile = async (file: File, albumId?: string): Promise<void> => {
      const validationError = validateFile(file);
      if (validationError) {
        throw new Error(validationError);
      }

      const fileExt = file.name.split('.').pop();
      const fileName = `${Date.now()}-${Math.random().toString(36).substring(2)}.${fileExt}`;
      const filePath = albumId ? `albums/${albumId}/${fileName}` : `photos/${fileName}`;

      // Upload to storage
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('photos')
        .upload(filePath, file);

      if (uploadError) {
        throw new Error(`업로드 실패: ${uploadError.message}`);
      }

      // Save metadata to database
      const { error: dbError } = await supabase
        .from('photos')
        .insert({
          filename: fileName,
          original_filename: file.name,
          file_path: uploadData.path,
          file_size: file.size,
          mime_type: file.type,
          album_id: albumId,
          user_id: user.id,
          is_favorite: false,
          tags: []
        });

      if (dbError) {
        // Clean up uploaded file if database insert fails
        await supabase.storage.from('photos').remove([filePath]);
        throw new Error(`데이터베이스 저장 실패: ${dbError.message}`);
      }
    };
    setIsUploading(true);
    
    // Initialize progress for all files
    const initialProgress: UploadProgress[] = files.map(file => ({
      fileName: file.name,
      progress: 0,
      status: 'pending'
    }));
    setUploadProgress(initialProgress);

    try {
      // Upload files sequentially to avoid overwhelming the server
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        setUploadProgress(prev => prev.map((item, index) => 
          index === i ? { ...item, status: 'uploading', progress: 0 } : item
        ));

        try {
          await uploadSingleFile(file, albumId);
          
          setUploadProgress(prev => prev.map((item, index) => 
            index === i ? { ...item, status: 'completed', progress: 100 } : item
          ));
        } catch (error) {
          setUploadProgress(prev => prev.map((item, index) => 
            index === i ? { 
              ...item, 
              status: 'error', 
              error: error instanceof Error ? error.message : '알 수 없는 오류'
            } : item
          ));
        }
      }
    } finally {
      setIsUploading(false);
    }
  }, [user]);

  const clearProgress = useCallback(() => {
    setUploadProgress([]);
  }, []);

  return {
    uploadFiles,
    uploadProgress,
    isUploading,
    clearProgress
  };
}