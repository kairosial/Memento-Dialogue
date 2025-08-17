-- Memento Box Database Seed Data
-- Sample data for development and testing

-- Insert sample CIST question templates
-- This data can be used by the application to generate contextual questions

-- Note: This is reference data only. 
-- Actual user data will be inserted through the application.

-- Sample CIST categories and scoring reference
INSERT INTO public.cist_categories (category, max_score, description) VALUES
('orientation_time', 4, '시간 지남력 - 연, 월, 일, 요일'),
('orientation_place', 1, '장소 지남력 - 현재 위치'),
('memory_registration', 3, '기억등록 - 문장 바로 따라하기'),
('memory_recall', 3, '기억회상 - 이전 문장 다시 말하기'),
('memory_recognition', 4, '기억재인 - 회상하지 못한 항목 재인'),
('attention', 1, '주의력 - 숫자나 단어 거꾸로 말하기'),
('executive_function', 2, '집행기능 - 언어추론'),
('language_naming', 3, '언어기능 - 이름대기')
ON CONFLICT DO NOTHING;

-- Sample question templates for each CIST category
-- These will be used to generate contextual questions during conversations

CREATE TABLE IF NOT EXISTS public.cist_question_templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    template_text TEXT NOT NULL,
    context_type VARCHAR(50) DEFAULT 'general',
    difficulty_level INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO public.cist_question_templates (category, template_text, context_type, difficulty_level) VALUES
-- Orientation - Time
('orientation_time', '오늘이 몇 년도인지 말씀해 주시겠어요?', 'general', 1),
('orientation_time', '오늘이 몇 월인지 아시나요?', 'general', 1),
('orientation_time', '오늘이 며칠인지 기억하시나요?', 'general', 1),
('orientation_time', '오늘이 무슨 요일인지 말씀해 주세요.', 'general', 1),

-- Orientation - Place
('orientation_place', '지금 어디에 계신지 말씀해 주시겠어요?', 'general', 1),
('orientation_place', '이곳이 어떤 장소인지 아시나요?', 'general', 1),

-- Memory - Registration
('memory_registration', '제가 말씀드리는 문장을 그대로 따라 말씀해 주세요: "나는 오늘 아침에 맛있는 밥을 먹었다"', 'general', 2),
('memory_registration', '이 문장을 따라 말씀해 주세요: "파란 하늘에 흰 구름이 떠 있다"', 'general', 2),

-- Memory - Recall
('memory_recall', '조금 전에 제가 말씀드린 문장을 기억해서 다시 말씀해 주시겠어요?', 'general', 3),

-- Memory - Recognition
('memory_recognition', '방금 전 문장에 이런 단어가 있었나요?', 'general', 3),

-- Attention
('attention', '제가 말하는 숫자를 거꾸로 말씀해 주세요: 1, 3, 5', 'general', 2),
('attention', '이 단어들을 거꾸로 말씀해 주실 수 있나요?', 'general', 2),

-- Executive Function
('executive_function', '과일 이름을 가능한 많이 말씀해 주시겠어요?', 'general', 2),
('executive_function', '채소 이름을 아는 대로 말씀해 주세요.', 'general', 2),

-- Language - Naming (Photo-based)
('language_naming', '이 사진에서 보이는 것이 무엇인지 말씀해 주세요.', 'photo', 1),
('language_naming', '사진 속 물건의 이름을 말씀해 주시겠어요?', 'photo', 1),
('language_naming', '이것이 무엇인지 아시나요?', 'photo', 1)
ON CONFLICT DO NOTHING;

-- Sample contextual conversation starters for photo-based reminiscence
CREATE TABLE IF NOT EXISTS public.conversation_starters (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    starter_text TEXT NOT NULL,
    context_type VARCHAR(50) DEFAULT 'general',
    emotion_tone VARCHAR(50) DEFAULT 'positive',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO public.conversation_starters (starter_text, context_type, emotion_tone) VALUES
('이 사진을 보니 어떤 기억이 떠오르시나요?', 'general', 'neutral'),
('이때는 언제쯤이었나요?', 'general', 'neutral'),
('누구와 함께 계셨나요?', 'general', 'positive'),
('이곳은 어디인가요?', 'general', 'neutral'),
('그때 기분이 어떠셨나요?', 'general', 'positive'),
('특별히 기억에 남는 일이 있으셨나요?', 'general', 'positive'),
('이 사진과 관련된 재미있는 이야기가 있으신가요?', 'general', 'positive'),
('가족들과 함께한 즐거운 시간이었나요?', 'family', 'positive'),
('이런 모임은 자주 가지셨나요?', 'social', 'positive'),
('음식이 맛있어 보이네요. 어떤 맛이었나요?', 'food', 'positive')
ON CONFLICT DO NOTHING;

-- Create views for easy data access
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

-- Sample configuration data
CREATE TABLE IF NOT EXISTS public.app_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO public.app_config (key, value, description) VALUES
('cist_scoring', '{"total_max_score": 21, "categories": {"orientation_time": 4, "orientation_place": 1, "memory_registration": 3, "memory_recall": 3, "memory_recognition": 4, "attention": 1, "executive_function": 2, "language_naming": 3}}', 'CIST scoring configuration'),
('session_settings', '{"max_photos_per_session": 5, "min_conversation_duration": 300, "max_conversation_duration": 1800}', 'Default session settings'),
('cognitive_thresholds', '{"normal": 18, "mild_concern": 15, "moderate_concern": 12, "high_concern": 0}', 'Cognitive status thresholds based on CIST scores')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    updated_at = NOW();