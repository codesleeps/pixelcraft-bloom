import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import time
from app.models.manager import ModelManager
from app.models.config import MODELS, ModelProvider

@pytest.fixture
async def model_manager():
    manager = ModelManager()
    await manager.initialize()
    yield manager
    await manager.cleanup()

@pytest.mark.asyncio
async def test_model_health_check(model_manager):
    """Test model availability checking"""
    # Mock session for controlled testing
    with patch.object(model_manager, '_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        # Mock that mistral:7b is available
        mock_response.json = AsyncMock(return_value={"models": [{"name": "mistral:7b"}]})
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Mock ollama_client.list_models directly since it might use its own session
        with patch.object(model_manager.ollama_client, 'list_models', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [{"name": "mistral:7b"}]
            
            await model_manager._check_model_availability()
            
            # Check that health checks were updated
            assert "mistral" in model_manager._health_checks
            assert model_manager._health_checks["mistral"] is True

@pytest.mark.asyncio
async def test_generate_with_caching(model_manager):
    """Test response caching"""
    prompt = "Test prompt"
    task_type = "chat"
    system_prompt = "Test system"
    
    # Mock available models to ensure we have one
    with patch.object(model_manager, 'get_available_models', return_value=[MODELS["mistral"]]):
        # Mock the generate method to return a response
        with patch.object(model_manager, '_generate_with_config', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Cached response"
            
            # First call - cache miss
            with patch.object(model_manager, '_get_cached_response', return_value=None):
                response1 = await model_manager.generate(prompt, task_type, system_prompt)
            
            # Second call - cache hit
            with patch.object(model_manager, '_get_cached_response', return_value="Cached response"):
                response2 = await model_manager.generate(prompt, task_type, system_prompt)
            
            assert response1 == "Cached response"
            assert response2 == "Cached response"
            # Should only call generate once due to caching (on the first call)
            assert mock_gen.call_count == 1

@pytest.mark.asyncio
async def test_automatic_failover(model_manager):
    """Test automatic failover when primary model fails"""
    task_type = "chat"
    
    # Mock get_available_models to return multiple models
    with patch.object(model_manager, 'get_available_models') as mock_get_models, \
         patch.object(model_manager, '_generate_with_config', new_callable=AsyncMock) as mock_gen:
        
        mock_get_models.return_value = [MODELS["mixtral"], MODELS["mistral"]]
        
        # First model fails, second succeeds
        mock_gen.side_effect = [Exception("Model failed"), "Success response"]
        
        response = await model_manager.generate("Test", task_type)
        
        assert response == "Success response"
        assert mock_gen.call_count == 2  # Called twice due to failover

@pytest.mark.asyncio
@pytest.mark.parametrize("task_type,prompt", [
    ("chat", "What services does AgentsFlowAI offer?"),
    ("code", "Write a Python function to calculate Fibonacci numbers"),
    ("lead_qualification", "Company: Acme Corp, Budget: $10k, Timeline: Q1 2026"),
    ("service_recommendation", "Client needs: E-commerce website with SEO"),
    ("web_development", "Build a landing page"),
    ("digital_marketing", "Create a social media strategy"),
    ("brand_design", "Design a logo"),
    ("ecommerce_solutions", "Set up an online store"),
    ("content_creation", "Write a blog post"),
    ("analytics_consulting", "Analyze website traffic")
])
async def test_all_task_types(model_manager, task_type, prompt):
    """Test generation for all supported task types"""
    # Mock get_available_models to ensure we have one
    with patch.object(model_manager, 'get_available_models', return_value=[MODELS["mistral"]]):
        with patch.object(model_manager, '_generate_with_config', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = f"Response for {task_type}"
            
            response = await model_manager.generate(
                prompt=prompt,
                task_type=task_type,
                system_prompt="You are an AI assistant for AgentsFlowAI."
            )
            
            assert response == f"Response for {task_type}"

@pytest.mark.asyncio
async def test_performance_benchmarking(model_manager):
    """Test performance metrics tracking"""
    prompt = "Benchmark prompt"
    task_type = "chat"
    
    # Mock Supabase for metrics persistence
    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = AsyncMock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute = mock_execute
    
    with patch.object(model_manager, 'supabase', mock_supabase), \
         patch.object(model_manager, 'get_available_models', return_value=[MODELS["mistral"]]), \
         patch.object(model_manager, '_generate_with_config', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Benchmark response"
        
        start_time = time.time()
        response = await model_manager.generate(prompt, task_type)
        end_time = time.time()
        
        # Check that metrics were updated
        assert "mistral:7b" in model_manager.metrics
        metrics = model_manager.metrics["mistral:7b"]
        assert metrics["requests"] >= 1
        assert metrics["successes"] >= 1
        assert metrics["total_latency"] > 0
        
        # Check that Supabase was called for persistence
        mock_execute.assert_called()

@pytest.mark.asyncio
async def test_error_handling_and_retries(model_manager):
    """Test error handling and circuit breaker"""
    task_type = "chat"
    
    with patch.object(model_manager, 'get_available_models') as mock_get_models, \
         patch.object(model_manager, '_generate_with_config', new_callable=AsyncMock) as mock_gen:
        
        mock_get_models.return_value = [MODELS["mistral"]]
        mock_gen.side_effect = Exception("Persistent failure")
        
        # Should handle failure gracefully
        response = await model_manager.generate("Test", task_type)
        assert "unable to process" in response.lower()
        
        # Check circuit breaker
        assert model_manager.circuit_breaker["mistral:7b"]["failures"] > 0

@pytest.mark.asyncio
async def test_ollama_provider(model_manager):
    """Test Ollama model generation"""
    # Mock chat since we provide a system prompt
    with patch.object(model_manager.ollama_client, 'chat', new_callable=AsyncMock) as mock_ollama:
        mock_ollama.return_value = {"message": {"content": "Ollama response"}}
        
        response = await model_manager._generate_ollama(
            "Test prompt", MODELS["mistral"], "System prompt"
        )
        
        assert response == "Ollama response"
        mock_ollama.assert_called_once()

@pytest.mark.asyncio
async def test_huggingface_provider(model_manager):
    """Test HuggingFace model generation"""
    # We don't have a HF model in default config, so we mock one
    hf_model = MODELS["mistral"].copy()
    hf_model.provider = ModelProvider.HUGGING_FACE
    hf_model.endpoint = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    
    with patch.object(model_manager, '_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{"generated_text": "HF response"}])
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        response = await model_manager._generate_huggingface(
            "Test prompt", hf_model, "System prompt"
        )
        
        assert response == "HF response"

@pytest.mark.asyncio
async def test_batch_generate(model_manager):
    """Test batch processing"""
    prompts = ["Prompt 1", "Prompt 2"]
    task_type = "chat"
    
    with patch.object(model_manager, 'generate', new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ["Response 1", "Response 2"]
        
        responses = await model_manager.batch_generate(prompts, task_type)
        
        assert responses == ["Response 1", "Response 2"]
        assert mock_gen.call_count == 2

@pytest.mark.asyncio
async def test_warm_up_models(model_manager):
    """Test model warm-up"""
    # Mock health checks to ensure at least one model is "healthy" so warm-up proceeds
    model_manager._health_checks["mistral"] = True
    
    with patch.object(model_manager.ollama_client, 'generate', new_callable=AsyncMock) as mock_warmup:
        mock_warmup.return_value = {"message": {"content": "Warm-up response"}}
        
        await model_manager.warm_up_models()
        
        # Should have called generate for available models
        assert mock_warmup.call_count > 0

@pytest.mark.asyncio
async def test_rate_limiting(model_manager):
    """Test rate limiting"""
    # Rate limiter allows 10 concurrent, test that it's respected
    assert model_manager.rate_limiter._value == 10

@pytest.mark.asyncio
async def test_get_available_models(model_manager):
    """Test intelligent model selection based on task type and health"""
    task_type = "chat"
    
    # Mock health checks
    model_manager._health_checks = {"mistral": True, "mixtral": False}
    
    available = model_manager.get_available_models(task_type)
    
    # Assuming MODEL_PRIORITIES["chat"] has mixtral and mistral in priority
    assert len(available) >= 1
    assert available[0].name == "mistral:7b" # mistral is fallback or second priority

@pytest.mark.asyncio
async def test_circuit_breaker_reset(model_manager):
    """Test circuit breaker automatic reset after timeout"""
    model_name = "mistral"
    
    # Simulate failures to open circuit
    for _ in range(6):
        model_manager._record_failure(model_name)
    
    assert model_manager._is_circuit_open(model_name)
    
    # Mock time to simulate passage of time
    with patch('time.time', return_value=time.time() + 61):  # 61 seconds later
        assert not model_manager._is_circuit_open(model_name)  # Should reset
