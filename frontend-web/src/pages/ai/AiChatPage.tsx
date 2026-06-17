import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Trash2, Sparkles, Volume2, VolumeX, ArrowLeft, ChevronRight, ChevronDown, ChevronUp, BookOpen, Calendar, Copy } from 'lucide-react';
import { useAiChatStore } from '../../stores/ai-chat-store';
import { useAuthStore } from '../../stores/auth-store';
import DigitalHumanModel from '../../components/DigitalHumanModel';
import ReactMarkdown from 'react-markdown';
