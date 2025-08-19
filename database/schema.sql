-- Memento Box Database Schema - Updated for T-003 Frontend Implementation
-- Supabase PostgreSQL Database
-- Updated: 2025-08-18 - Includes photo upload and album management features

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    birth_date DATE,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    phone VARCHAR(20),
    profile_image_url TEXT,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    privacy_consent BOOLEAN DEFAULT FALSE,
    terms_accepted BOOLEAN DEFAULT FALSE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Albums table (NEW - for photo organization)
CREATE TABLE public.albums (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Photos table (UPDATED - compatible with frontend implementation)
CREATE TABLE public.photos (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    -- Original filename-related fields
    file_name VARCHAR(255) NOT NULL,                    -- Legacy field (kept for compatibility)
    filename VARCHAR(255) NOT NULL,                     -- NEW: Used by frontend upload hook
    original_filename VARCHAR(255) NOT NULL,            -- NEW: Original user filename
    -- File storage and metadata
    file_path TEXT NOT NULL,                            -- Supabase storage path
    file_size BIGINT,                                   -- UPDATED: INTEGER → BIGINT for larger files
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    -- Content and categorization
    description TEXT,
    tags TEXT[], -- Array of tags for photo categorization
    album_id UUID REFERENCES public.albums(id) ON DELETE SET NULL,  -- NEW: Album association
    -- Location and timing
    taken_at TIMESTAMP WITH TIME ZONE,
    location_name VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    -- Status flags
    is_favorite BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversation sessions table
CREATE TABLE public.sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    session_type VARCHAR(50) DEFAULT 'reminiscence' CHECK (session_type IN ('reminiscence', 'assessment', 'mixed')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
    selected_photos UUID[] NOT NULL, -- Array of photo IDs used in this session
    total_duration_seconds INTEGER DEFAULT 0,
    cist_score INTEGER, -- Total CIST score (0-21)
    cist_completed_items INTEGER DEFAULT 0, -- Number of CIST items completed
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual conversations within a session
CREATE TABLE public.conversations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    photo_id UUID REFERENCES public.photos(id) ON DELETE SET NULL,
    conversation_order INTEGER NOT NULL, -- Order within the session
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL CHECK (question_type IN ('open_ended', 'cist_orientation', 'cist_memory', 'cist_attention', 'cist_executive', 'cist_language')),
    cist_category VARCHAR(50), -- Specific CIST category if applicable
    user_response_text TEXT,
    user_response_audio_url TEXT,
    response_duration_seconds INTEGER,
    ai_analysis JSONB, -- AI analysis results stored as JSON
    cist_score INTEGER, -- Score for this specific CIST item (if applicable)
    is_cist_item BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CIST assessment responses (detailed tracking)
CREATE TABLE public.cist_responses (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    cist_category VARCHAR(50) NOT NULL CHECK (cist_category IN ('orientation_time', 'orientation_place', 'memory_registration', 'memory_recall', 'memory_recognition', 'attention', 'executive_function', 'language_naming')),
    question_text TEXT NOT NULL,
    expected_response TEXT, -- What the correct response should be
    user_response TEXT,
    is_correct BOOLEAN,
    partial_score DECIMAL(3,2), -- For partial credit (0.00 to 1.00)
    response_time_seconds INTEGER,
    difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level BETWEEN 1 AND 5),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Session reports (generated summaries)
CREATE TABLE public.session_reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    total_cist_score INTEGER NOT NULL,
    max_possible_score INTEGER DEFAULT 21,
    cognitive_status VARCHAR(50) CHECK (cognitive_status IN ('normal', 'mild_concern', 'moderate_concern', 'high_concern')),
    category_scores JSONB, -- Detailed scores by CIST category
    insights TEXT[], -- Array of AI-generated insights
    recommendations TEXT[], -- Array of recommendations
    report_generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_shared BOOLEAN DEFAULT FALSE,
    shared_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CIST question templates (NEW - for AI-driven question generation)
CREATE TABLE public.cist_question_templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    template_text TEXT NOT NULL,
    context_type VARCHAR(50) DEFAULT 'general',
    difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level BETWEEN 1 AND 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversation starters (NEW - for photo-based reminiscence)
CREATE TABLE public.conversation_starters (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    starter_text TEXT NOT NULL,
    context_type VARCHAR(50) DEFAULT 'general',
    emotion_tone VARCHAR(50) DEFAULT 'positive',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- App configuration (NEW - for runtime settings)
CREATE TABLE public.app_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance optimization
-- Users indexes
CREATE INDEX idx_users_email ON public.users(email);

-- Albums indexes
CREATE INDEX idx_albums_user_id ON public.albums(user_id);
CREATE INDEX idx_albums_name ON public.albums(user_id, name);

-- Photos indexes
CREATE INDEX idx_photos_user_id ON public.photos(user_id);
CREATE INDEX idx_photos_album_id ON public.photos(album_id);
CREATE INDEX idx_photos_created_at ON public.photos(created_at DESC);
CREATE INDEX idx_photos_tags ON public.photos USING GIN(tags);
CREATE INDEX idx_photos_filename ON public.photos(filename);
CREATE INDEX idx_photos_is_favorite ON public.photos(user_id, is_favorite) WHERE is_favorite = true;
CREATE INDEX idx_photos_is_deleted ON public.photos(is_deleted) WHERE is_deleted = false;

-- Sessions indexes
CREATE INDEX idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX idx_sessions_status ON public.sessions(status);
CREATE INDEX idx_sessions_started_at ON public.sessions(started_at DESC);

-- Conversations indexes
CREATE INDEX idx_conversations_session_id ON public.conversations(session_id);
CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX idx_conversations_question_type ON public.conversations(question_type);

-- CIST responses indexes
CREATE INDEX idx_cist_responses_session_id ON public.cist_responses(session_id);
CREATE INDEX idx_cist_responses_user_id ON public.cist_responses(user_id);
CREATE INDEX idx_cist_responses_category ON public.cist_responses(cist_category);

-- Session reports indexes
CREATE INDEX idx_session_reports_user_id ON public.session_reports(user_id);

-- CIST question templates indexes
CREATE INDEX idx_cist_templates_category ON public.cist_question_templates(category);
CREATE INDEX idx_cist_templates_context ON public.cist_question_templates(context_type);

-- Row Level Security (RLS) Policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.albums ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cist_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_reports ENABLE ROW LEVEL SECURITY;
-- Note: Reference tables (cist_question_templates, conversation_starters, app_config) are publicly readable

-- Users policies
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Albums policies
CREATE POLICY "Users can view own albums" ON public.albums
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own albums" ON public.albums
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own albums" ON public.albums
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own albums" ON public.albums
    FOR DELETE USING (auth.uid() = user_id);

-- Photos policies
CREATE POLICY "Users can view own photos" ON public.photos
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own photos" ON public.photos
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own photos" ON public.photos
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own photos" ON public.photos
    FOR DELETE USING (auth.uid() = user_id);

-- Sessions policies
CREATE POLICY "Users can view own sessions" ON public.sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions" ON public.sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON public.sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- Conversations policies
CREATE POLICY "Users can view own conversations" ON public.conversations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversations" ON public.conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations" ON public.conversations
    FOR UPDATE USING (auth.uid() = user_id);

-- CIST responses policies
CREATE POLICY "Users can view own cist responses" ON public.cist_responses
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own cist responses" ON public.cist_responses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Session reports policies
CREATE POLICY "Users can view own reports" ON public.session_reports
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own reports" ON public.session_reports
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Functions for updated_at timestamps
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

CREATE TRIGGER albums_updated_at
    BEFORE UPDATE ON public.albums
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

CREATE TRIGGER photos_updated_at
    BEFORE UPDATE ON public.photos
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

CREATE TRIGGER sessions_updated_at
    BEFORE UPDATE ON public.sessions
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

CREATE TRIGGER conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

CREATE TRIGGER app_config_updated_at
    BEFORE UPDATE ON public.app_config
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

-- Storage bucket policies (to be applied in Supabase dashboard or via SQL)
-- Note: These policies require the storage.objects table to exist

-- Create all storage buckets (PRIVATE for security)
INSERT INTO storage.buckets (id, name, public) VALUES
('memento-storage', 'memento-storage', false),
('photos', 'photos', false)
ON CONFLICT (id) DO UPDATE SET
  public = EXCLUDED.public;

-- Storage policies for memento-storage bucket (general files)
CREATE POLICY "Users can upload own files to memento-storage" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'memento-storage' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view own files in memento-storage" ON storage.objects
  FOR SELECT USING (bucket_id = 'memento-storage' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can update own files in memento-storage" ON storage.objects
  FOR UPDATE USING (bucket_id = 'memento-storage' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete own files in memento-storage" ON storage.objects
  FOR DELETE USING (bucket_id = 'memento-storage' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Storage policies for photos bucket (T-003 implementation)
CREATE POLICY "Users can upload own photos" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view own photos" ON storage.objects
  FOR SELECT USING (bucket_id = 'photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can update own photos" ON storage.objects
  FOR UPDATE USING (bucket_id = 'photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete own photos" ON storage.objects
  FOR DELETE USING (bucket_id = 'photos' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Helpful views for common queries
CREATE OR REPLACE VIEW public.user_album_summary AS
SELECT 
    a.id as album_id,
    a.name as album_name,
    a.description,
    a.user_id,
    COUNT(p.id) as photo_count,
    MAX(p.created_at) as last_photo_added
FROM public.albums a
LEFT JOIN public.photos p ON a.id = p.album_id AND p.is_deleted = false
GROUP BY a.id, a.name, a.description, a.user_id;

CREATE OR REPLACE VIEW public.user_session_summary AS
SELECT 
    u.id as user_id,
    u.full_name,
    u.email,
    COUNT(s.id) as total_sessions,
    AVG(s.cist_score) as avg_cist_score,
    MAX(s.started_at) as last_session_date,
    SUM(s.total_duration_seconds) as total_conversation_time
FROM public.users u
LEFT JOIN public.sessions s ON u.id = s.user_id
WHERE s.status = 'completed'
GROUP BY u.id, u.full_name, u.email;

CREATE OR REPLACE VIEW public.cist_performance_by_category AS
SELECT 
    cr.user_id,
    cr.cist_category,
    COUNT(*) as total_attempts,
    AVG(cr.partial_score) as avg_score,
    COUNT(CASE WHEN cr.is_correct = true THEN 1 END) as correct_answers
FROM public.cist_responses cr
GROUP BY cr.user_id, cr.cist_category;

-- Comments for documentation
COMMENT ON TABLE public.albums IS 'Photo albums for organizing user photos - NEW in T-003';
COMMENT ON COLUMN public.photos.filename IS 'Generated unique filename for storage - NEW in T-003';
COMMENT ON COLUMN public.photos.original_filename IS 'Original user-uploaded filename - NEW in T-003';
COMMENT ON COLUMN public.photos.file_size IS 'File size in bytes (BIGINT for large files) - UPDATED in T-003';
COMMENT ON COLUMN public.photos.album_id IS 'Reference to albums table - NEW in T-003';

-- Schema version tracking
INSERT INTO public.app_config (key, value, description) VALUES
('schema_version', '"1.1.0"', 'Database schema version - T-003 implementation'),
('last_updated', '"2025-08-18"', 'Last schema update date'),
('features', '["photo_upload", "album_management", "drag_drop", "file_preview", "progress_tracking"]', 'Implemented features in current version')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    updated_at = NOW();