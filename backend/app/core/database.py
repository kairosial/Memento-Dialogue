from supabase import create_client, Client
from .config import settings

# Supabase client instance
supabase: Client = create_client(
    supabase_url=settings.supabase_url,
    supabase_key=settings.supabase_anon_key
)

# Service role client for admin operations
supabase_admin: Client = create_client(
    supabase_url=settings.supabase_url,
    supabase_key=settings.supabase_service_role_key
)