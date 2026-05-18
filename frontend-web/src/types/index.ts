// ===== API Response Wrapper =====
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

// ===== User =====
export interface User {
  id: number;
  username: string;
  nickname: string;
  avatar_url: string;
  role: string;
  preferred_heritage_types: string;
  preferred_scene_types: string;
  preferred_regions: string;
  confidence_score: number;
}

export interface Session {
  userId: number;
  username: string;
  nickname: string;
  role: string;
  token?: string;
}

// ===== Content (非遗内容) =====
export interface ContentItem {
  id: number;
  title: string;
  summary: string;
  content: string;
  cover_url: string;
  category: string;
  region: string;
  tags: string[];
  chapter?: string;
  sub_chapter?: string;
  source_site?: string;
  quality_score?: number;
  is_featured?: number;
  status?: string;
  view_count?: number;
  like_count?: number;
  favorite_count?: number;
  created_at: string;
  // Recommendation fields
  reason?: string;
  snippet?: string;
  explain?: RecommendExplain;
}

// ===== Activity (活动) =====
export interface Activity {
  id: number;
  title: string;
  description: string;
  cover_url: string;
  location: string;
  start_time: string;
  end_time: string;
  category: string;
  status: string;
  organizer?: string;
  max_participants?: number;
  current_participants?: number;
  is_featured?: number;
  created_at: string;
  reason?: string;
  snippet?: string;
  explain?: RecommendExplain;
}

// ===== Discussion (社区讨论) =====
export interface DiscussionTopic {
  id: number;
  title: string;
  content: string;
  cover_url: string;
  image_urls: string;
  nickname: string;
  category: string;
  tags: string[];
  like_count: number;
  favorite_count: number;
  comment_count: number;
  is_featured?: number;
  created_at: string;
  reason?: string;
  snippet?: string;
  explain?: RecommendExplain;
}

// ===== Recommend =====
export interface RecommendData {
  guide_text: string;
  contents: ContentItem[];
  events: Activity[];
  topics: DiscussionTopic[];
  profile_summary?: ProfileSummary;
  crs_state?: CrsState;
  scene?: string;
}

export interface ProfileSummary {
  summary_text: string;
  sources: string[];
}

export interface CrsState {
  mode: string;
  confidence_score: number;
  confidence_score_raw: number;
  stage_progress_percent: number;
  need_cold_start: boolean;
  session_id?: string;
  turn_count?: number;
  dimensions?: Record<string, number>;
  ask_timeline?: AskLog[];
  recommend_cards?: RecommendCard[];
}

export interface AskLog {
  ask_id: string;
  attribute: string;
  question_text: string;
  answer?: string;
  score_delta?: number;
}

// ===== Recommend Card (used in AI chat) =====
export interface RecommendCard {
  id: number;
  type: 'content' | 'event' | 'topic';
  title: string;
  cover_url?: string;
  summary?: string;
  reason: string;
  explain: RecommendExplain;
}

export interface RecommendExplain {
  match_score?: number;
  match_score_text?: string;
  final_score?: number;
  final_score_text?: string;
  novelty_score?: number;
  novelty_score_text?: string;
  diversity_penalty?: number;
  diversity_penalty_text?: string;
  kg_score?: number;
  kg_score_text?: string;
  kg_reason?: string;
  kg_path_text?: string;
  crs_mode_label?: string;
  strategy_context?: {
    sources?: string[];
    heritage_terms?: string[];
  };
  kg_context?: {
    similar_entities?: string[];
    expand_path?: string;
    kg_reason?: string;
  };
  match_detail?: Record<string, number>;
  display?: {
    matchDetailText: string;
    sources: string[];
    heritageTerms: string[];
    similarEntities: string[];
    expandPath: string;
    kgReasonText: string;
  };
}

// ===== AI Chat =====
export interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  text: string;
  isTransition?: boolean;
}

export interface ActionTask {
  id: string;
  title: string;
  desc: string;
  type: 'content' | 'event' | 'topic';
  targetId: number;
  done: boolean;
  recommended?: boolean;
  metaTitle?: string;
}

export interface AiChatResponse {
  answer: string;
  source: string;
  recommend_cards: RecommendCard[];
  crs_mode?: string;
  crs_confidence?: {
    mode: string;
    confidence_score: number;
    dimensions: Record<string, number>;
  };
  crs_session_id?: string;
  recommended_questions?: string[];
  followup_questions?: string[];
  search_web?: boolean;
  ask_prompt?: string;
  ask_options?: string[];
  ask_id?: string;
  ask_attribute?: string;
  strategy?: string;
  strategy_display?: string;
  strategy_note?: string;
  kg_entity?: string;
  kg_similar?: { items: { entity: string }[] };
  kg_expand?: { items: { entity: string }[] };
  kg_path?: { path: { entity?: string; relation?: string }[] };
  transition_msg?: string;
  profile_summary?: {
    summary_text: string;
    sources: string[];
  };
  recommend_prefix?: string;
  rewrite_suggestions?: string[];
}

export interface CrsAnswerResponse {
  mode: string;
  confidence_score: number;
  dimensions: Record<string, number>;
  ask_timeline: AskLog[];
  recommend_cards: RecommendCard[];
  transition_msg?: string;
  session_id?: string;
}

// ===== Stats (Admin) =====
export interface DashboardStats {
  total_users: number;
  total_contents: number;
  total_activities: number;
  total_discussions: number;
  total_knowledge_base: number;
  users_today: number;
  contents_approved: number;
  activities_open: number;
}
