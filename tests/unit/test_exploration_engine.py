"""
Unit tests for Exploration Engine
=================================

Tests the web exploration and curiosity-driven discovery system.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock, call
import pytest
import random

from src.exploration.engine import InterestTracker, RateLimiter, WebExplorer
from src.core.orchestrator import SystemState
from src.safety.core_safety import SafetyFramework, Action


@pytest.fixture
def interest_tracker():
    """Create test interest tracker"""
    return InterestTracker()


@pytest.fixture
def rate_limiter():
    """Create test rate limiter"""
    return RateLimiter(requests_per_minute=10)


@pytest.fixture
def mock_safety_framework():
    """Create mock safety framework"""
    framework = AsyncMock(spec=SafetyFramework)
    framework.validate_action = AsyncMock(return_value=(True, None))
    return framework


@pytest.fixture
def web_explorer(mock_safety_framework):
    """Create test web explorer"""
    explorer = WebExplorer("WebExplorer")
    explorer.safety_framework = mock_safety_framework
    return explorer


class TestInterestTracker:
    """Test interest tracking functionality"""
    
    def test_initialization(self, interest_tracker):
        """Test interest tracker initialization"""
        assert len(interest_tracker.interests) == 5
        assert 'consciousness' in interest_tracker.interests
        assert interest_tracker.interests['consciousness']['weight'] == 0.9
        assert interest_tracker.interests['consciousness']['last_explored'] is None
        assert interest_tracker.user_interests == {}
        assert interest_tracker.discovered_topics == []
    
    @pytest.mark.asyncio
    async def test_get_next_topic_unvisited(self, interest_tracker):
        """Test getting next topic when none have been visited"""
        # Mock random.choices to return predictable result
        with patch('random.choices', return_value=['consciousness']):
            topic = await interest_tracker.get_next_topic()
            assert topic == 'consciousness'
            assert interest_tracker.interests['consciousness']['last_explored'] is not None
    
    @pytest.mark.asyncio
    async def test_get_next_topic_with_history(self, interest_tracker):
        """Test getting next topic with exploration history"""
        # Mark some topics as recently explored
        current_time = datetime.now()
        interest_tracker.interests['consciousness']['last_explored'] = current_time
        interest_tracker.interests['artificial_intelligence']['last_explored'] = current_time - timedelta(hours=2)
        
        # Should select from unexplored or old topics
        topic = await interest_tracker.get_next_topic()
        assert topic is not None
        assert topic != 'consciousness'  # Too recent
    
    @pytest.mark.asyncio
    async def test_get_next_topic_all_recent(self, interest_tracker):
        """Test when all topics were recently explored"""
        current_time = datetime.now()
        for topic in interest_tracker.interests:
            interest_tracker.interests[topic]['last_explored'] = current_time
        
        topic = await interest_tracker.get_next_topic()
        assert topic is None
    
    def test_add_user_interest_new(self, interest_tracker):
        """Test adding new user interest"""
        interest_tracker.add_user_interest("quantum_computing", 0.7)
        
        assert "quantum_computing" in interest_tracker.interests
        assert interest_tracker.interests["quantum_computing"]["weight"] == 0.7
        assert interest_tracker.interests["quantum_computing"]["last_explored"] is None
    
    def test_add_user_interest_existing(self, interest_tracker):
        """Test increasing weight of existing interest"""
        original_weight = interest_tracker.interests['consciousness']['weight']
        interest_tracker.add_user_interest("consciousness")
        
        new_weight = interest_tracker.interests['consciousness']['weight']
        assert new_weight == min(1.0, original_weight + 0.1)
    
    def test_add_user_interest_max_weight(self, interest_tracker):
        """Test weight capping at 1.0"""
        interest_tracker.interests['consciousness']['weight'] = 0.95
        interest_tracker.add_user_interest("consciousness")
        
        assert interest_tracker.interests['consciousness']['weight'] == 1.0
    
    def test_discover_topic_relevant(self, interest_tracker):
        """Test discovering relevant topic"""
        interest_tracker.discover_topic("AI consciousness theories", "web_search")
        
        assert len(interest_tracker.discovered_topics) == 1
        discovered = interest_tracker.discovered_topics[0]
        assert discovered['topic'] == "AI consciousness theories"
        assert discovered['source'] == "web_search"
        assert isinstance(discovered['timestamp'], datetime)
        
        # Should be added to interests
        assert "AI consciousness theories" in interest_tracker.interests
        assert interest_tracker.interests["AI consciousness theories"]["weight"] == 0.4
    
    def test_discover_topic_irrelevant(self, interest_tracker):
        """Test discovering irrelevant topic"""
        interest_tracker.discover_topic("weather patterns", "web_search")
        
        assert len(interest_tracker.discovered_topics) == 1
        # Should not be added to interests
        assert "weather patterns" not in interest_tracker.interests


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_initialization(self, rate_limiter):
        """Test rate limiter initialization"""
        assert rate_limiter.requests_per_minute == 10
        assert rate_limiter.request_times == []
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_empty(self, rate_limiter):
        """Test rate limit check with no previous requests"""
        allowed = await rate_limiter.check_rate_limit()
        assert allowed is True
        assert len(rate_limiter.request_times) == 1
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self, rate_limiter):
        """Test rate limit check within limits"""
        # Add some requests
        current_time = datetime.now()
        for i in range(5):
            rate_limiter.request_times.append(current_time - timedelta(seconds=i*10))
        
        allowed = await rate_limiter.check_rate_limit()
        assert allowed is True
        assert len(rate_limiter.request_times) == 6
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit check when limit exceeded"""
        # Add requests at limit
        current_time = datetime.now()
        for i in range(10):
            rate_limiter.request_times.append(current_time - timedelta(seconds=i))
        
        allowed = await rate_limiter.check_rate_limit()
        assert allowed is False
        # Should not add new request time when denied
        assert len(rate_limiter.request_times) == 10
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_cleanup_old(self, rate_limiter):
        """Test cleanup of old request times"""
        # Add old requests
        current_time = datetime.now()
        for i in range(5):
            rate_limiter.request_times.append(current_time - timedelta(minutes=2))
        
        # Add recent requests
        for i in range(3):
            rate_limiter.request_times.append(current_time - timedelta(seconds=i))
        
        allowed = await rate_limiter.check_rate_limit()
        assert allowed is True
        # Old requests should be cleaned up
        assert len(rate_limiter.request_times) == 4  # 3 recent + 1 new


class TestWebExplorer:
    """Test web explorer functionality"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, web_explorer):
        """Test web explorer initialization"""
        await web_explorer.initialize()
        
        assert isinstance(web_explorer.interest_tracker, InterestTracker)
        assert isinstance(web_explorer.rate_limiter, RateLimiter)
        assert web_explorer.exploration_active is False
    
    @pytest.mark.asyncio
    async def test_handle_message_start_exploration(self, web_explorer):
        """Test handling start exploration message"""
        await web_explorer.initialize()
        
        message = Mock(type="start_exploration", content={"topic": "AI ethics"})
        
        with patch.object(web_explorer, 'explore_topic', new_callable=AsyncMock) as mock_explore:
            await web_explorer.handle_message(message)
            mock_explore.assert_called_once_with("AI ethics")
    
    @pytest.mark.asyncio
    async def test_handle_message_user_interest(self, web_explorer):
        """Test handling user interest message"""
        await web_explorer.initialize()
        
        message = Mock(type="user_interest", content={"topic": "quantum computing", "weight": 0.8})
        
        await web_explorer.handle_message(message)
        
        assert "quantum computing" in web_explorer.interest_tracker.interests
        assert web_explorer.interest_tracker.interests["quantum computing"]["weight"] == 0.8
    
    @pytest.mark.asyncio
    async def test_service_name(self, web_explorer):
        """Test service name"""
        assert web_explorer.service_name == "WebExplorer"