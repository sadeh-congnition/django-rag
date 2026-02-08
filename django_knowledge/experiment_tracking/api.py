from ninja import NinjaAPI, Schema
from django.utils import timezone
from typing import Optional, List
from .models import EmbedderEval, EmbeddingModel, MetricConfig, EmbedderPerformance


class EmbeddingModelSchema(Schema):
    id: int
    name: str
    url: str
    created_at: str
    updated_at: str


class MetricConfigSchema(Schema):
    id: int
    content: dict
    created_at: str
    updated_at: str


class EmbedderPerformanceSchema(Schema):
    id: int
    search_time: float
    embedding_time: float
    embedding_model: Optional[EmbeddingModelSchema] = None
    created_at: str
    updated_at: str


class EmbedderEvalSchema(Schema):
    id: int
    name: str
    description: str
    score: float
    score_percentage: float
    embedding_model: EmbeddingModelSchema
    chunk_config: Optional[dict] = None
    metric_config: Optional[MetricConfigSchema] = None
    embedder_performance: Optional[EmbedderPerformanceSchema] = None
    created_at: str
    updated_at: str


api = NinjaAPI()


@api.get("/evaluations", response=List[EmbedderEvalSchema])
def list_evaluations(request):
    """
    Returns a list of all EmbedderEval evaluations with their related data.
    """
    evaluations = EmbedderEval.objects.select_related(
        "embedding_model",
        "metric_config", 
        "embedder_performance",
        "embedder_performance__embedding_model"
    ).prefetch_related(
        "chunk_config"
    ).all().order_by("-created_at")
    
    result = []
    for eval in evaluations:
        # Prepare chunk_config data
        chunk_config_data = None
        if eval.chunk_config:
            chunk_config_data = {
                "id": eval.chunk_config.id,
                "content": eval.chunk_config.content,
                "created_at": eval.chunk_config.created_at.isoformat(),
                "updated_at": eval.chunk_config.updated_at.isoformat(),
            }
        
        # Prepare embedding model data
        embedding_model_data = {
            "id": eval.embedding_model.id,
            "name": eval.embedding_model.name,
            "url": eval.embedding_model.url,
            "created_at": eval.embedding_model.created_at.isoformat(),
            "updated_at": eval.embedding_model.updated_at.isoformat(),
        }
        
        # Prepare metric config data
        metric_config_data = None
        if eval.metric_config:
            metric_config_data = {
                "id": eval.metric_config.id,
                "content": eval.metric_config.content,
                "created_at": eval.metric_config.created_at.isoformat(),
                "updated_at": eval.metric_config.updated_at.isoformat(),
            }
        
        # Prepare embedder performance data
        embedder_performance_data = None
        if eval.embedder_performance:
            perf_embedding_model_data = None
            if eval.embedder_performance.embedding_model:
                perf_embedding_model_data = {
                    "id": eval.embedder_performance.embedding_model.id,
                    "name": eval.embedder_performance.embedding_model.name,
                    "url": eval.embedder_performance.embedding_model.url,
                    "created_at": eval.embedder_performance.embedding_model.created_at.isoformat(),
                    "updated_at": eval.embedder_performance.embedding_model.updated_at.isoformat(),
                }
            
            embedder_performance_data = {
                "id": eval.embedder_performance.id,
                "search_time": eval.embedder_performance.search_time,
                "embedding_time": eval.embedder_performance.embedding_time,
                "embedding_model": perf_embedding_model_data,
                "created_at": eval.embedder_performance.created_at.isoformat(),
                "updated_at": eval.embedder_performance.updated_at.isoformat(),
            }
        
        # Calculate score percentage
        score_percentage = 0.0
        if eval.metric_config and hasattr(eval.metric_config, 'num_tests'):
            try:
                num_tests = eval.metric_config.num_tests()
                if num_tests > 0:
                    score_percentage = (eval.score / num_tests) * 100
            except (AttributeError, TypeError, ZeroDivisionError):
                score_percentage = 0.0
        
        result.append({
            "id": eval.id,
            "name": eval.name,
            "description": eval.description,
            "score": eval.score,
            "score_percentage": round(score_percentage, 1),
            "embedding_model": embedding_model_data,
            "chunk_config": chunk_config_data,
            "metric_config": metric_config_data,
            "embedder_performance": embedder_performance_data,
            "created_at": eval.created_at.isoformat(),
            "updated_at": eval.updated_at.isoformat(),
        })
    
    return result
