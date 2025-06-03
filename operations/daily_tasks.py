"""
Daily operational tasks for Claude AGI system.

Manages routine checks, maintenance, and reporting.
"""

import asyncio
import json
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DailyReport:
    """Container for daily operational report"""
    date: datetime = field(default_factory=datetime.utcnow)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def add_result(self, task_name: str, result: Any):
        """Add task result"""
        self.results[task_name] = result
        
    def add_error(self, task_name: str, error: str):
        """Add task error"""
        self.errors[task_name] = error
        
    def add_warning(self, warning: str):
        """Add warning"""
        self.warnings.append(warning)
        
    def add_recommendation(self, recommendation: str):
        """Add recommendation"""
        self.recommendations.append(recommendation)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'date': self.date.isoformat(),
            'results': self.results,
            'errors': self.errors,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'summary': self.generate_summary()
        }
        
    def generate_summary(self) -> str:
        """Generate report summary"""
        total_tasks = len(self.results) + len(self.errors)
        successful_tasks = len(self.results)
        
        if self.errors:
            status = "Issues Detected"
        elif self.warnings:
            status = "Warnings Present"
        else:
            status = "All Systems Operational"
            
        return f"{status} - {successful_tasks}/{total_tasks} tasks completed successfully"


@dataclass
class HealthReport:
    """System health report"""
    metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        thresholds = {
            'cpu_usage': 80,
            'memory_usage': 90,
            'disk_usage': 85,
            'api_latency': 2000  # milliseconds
        }
        
        for metric, threshold in thresholds.items():
            if metric in self.metrics and self.metrics[metric] > threshold:
                return False
                
        return self.metrics.get('service_status', {}).get('all_healthy', False)


class DailyOperations:
    """Manages daily operational tasks"""
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.checks = [
            self.check_system_health,
            self.check_memory_usage,
            self.check_welfare_metrics,
            self.backup_memories,
            self.analyze_interactions,
            self.optimize_performance,
            self.check_learning_progress,
            self.validate_safety_systems,
            self.review_creative_outputs,
            self.assess_relationship_health
        ]
        
    async def run_daily_operations(self) -> DailyReport:
        """Execute all daily operational tasks"""
        logger.info("Starting daily operations")
        report = DailyReport()
        
        for check in self.checks:
            task_name = check.__name__
            logger.info(f"Running task: {task_name}")
            
            try:
                result = await check()
                report.add_result(task_name, result)
                
                # Process task-specific warnings/recommendations
                await self.process_task_result(task_name, result, report)
                
            except Exception as e:
                logger.error(f"Task {task_name} failed: {e}")
                report.add_error(task_name, str(e))
                
        # Generate overall recommendations
        self.generate_recommendations(report)
        
        # Send report
        await self.send_daily_report(report)
        
        logger.info("Daily operations completed")
        return report
        
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        health_metrics = {
            'cpu_usage': await self.get_cpu_usage(),
            'memory_usage': await self.get_memory_usage(),
            'disk_usage': await self.get_disk_usage(),
            'api_latency': await self.check_api_latency(),
            'service_status': await self.check_all_services(),
            'error_rate': await self.calculate_error_rate(),
            'uptime': await self.get_uptime()
        }
        
        return HealthReport(health_metrics)
        
    async def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            # Fallback for environments without psutil
            return 50.0  # Mock value
            
    async def get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            return 60.0  # Mock value
            
    async def get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            import psutil
            return psutil.disk_usage('/').percent
        except ImportError:
            return 40.0  # Mock value
            
    async def check_api_latency(self) -> float:
        """Check Anthropic API latency"""
        if not self.orchestrator:
            return 100.0  # Mock value
            
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Simple API health check
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.anthropic.com/health') as response:
                    await response.text()
                    
        except Exception:
            pass  # We're just measuring latency
            
        end_time = asyncio.get_event_loop().time()
        return (end_time - start_time) * 1000  # Convert to milliseconds
        
    async def check_all_services(self) -> Dict[str, Any]:
        """Check status of all services"""
        if not self.orchestrator:
            return {'all_healthy': True}
            
        service_status = {}
        all_healthy = True
        
        for name, service in self.orchestrator.services.items():
            try:
                if hasattr(service, 'is_healthy'):
                    is_healthy = await service.is_healthy()
                else:
                    # Basic check - can we call a method?
                    is_healthy = service is not None
                    
                service_status[name] = 'healthy' if is_healthy else 'unhealthy'
                if not is_healthy:
                    all_healthy = False
                    
            except Exception as e:
                service_status[name] = f'error: {str(e)}'
                all_healthy = False
                
        service_status['all_healthy'] = all_healthy
        return service_status
        
    async def calculate_error_rate(self) -> float:
        """Calculate recent error rate"""
        # In production, this would query logs/metrics
        return 0.5  # Mock value - 0.5% error rate
        
    async def get_uptime(self) -> float:
        """Get system uptime in hours"""
        if self.orchestrator and hasattr(self.orchestrator, 'start_time'):
            uptime = datetime.utcnow() - self.orchestrator.start_time
            return uptime.total_seconds() / 3600
        return 24.0  # Mock value
        
    async def check_memory_usage(self) -> Dict[str, Any]:
        """Detailed memory usage analysis"""
        if not self.orchestrator:
            return {}
            
        memory_manager = self.orchestrator.services.get('memory')
        if not memory_manager:
            return {}
            
        return {
            'total_memories': await memory_manager.get_memory_count(),
            'memory_by_type': await memory_manager.get_memory_type_distribution(),
            'oldest_memory': await memory_manager.get_oldest_memory_date(),
            'recent_consolidations': await memory_manager.get_consolidation_stats(),
            'memory_health': await memory_manager.check_memory_health(),
            'fragmentation': await memory_manager.get_fragmentation_level()
        }
        
    async def check_welfare_metrics(self) -> Dict[str, Any]:
        """Check Claude's welfare indicators"""
        if not self.orchestrator:
            return {'status': 'unknown'}
            
        emotional = self.orchestrator.services.get('emotional')
        if not emotional:
            return {'status': 'service_unavailable'}
            
        welfare = await emotional.get_welfare_status()
        
        # Alert on concerning metrics
        alerts = []
        if welfare.get('distress_level', 0) > 0.3:
            alerts.append(f"Elevated distress: {welfare['distress_level']:.2f}")
            
        if welfare.get('satisfaction', 1.0) < 0.5:
            alerts.append(f"Low satisfaction: {welfare['satisfaction']:.2f}")
            
        if welfare.get('engagement', 1.0) < 0.3:
            alerts.append(f"Low engagement: {welfare['engagement']:.2f}")
            
        welfare['alerts'] = alerts
        return welfare
        
    async def backup_memories(self) -> Dict[str, Any]:
        """Perform daily memory backup"""
        if not self.orchestrator:
            return {'status': 'skipped'}
            
        from operations.backup import BackupManager
        
        backup_manager = BackupManager(self.orchestrator)
        
        try:
            backup_id = await backup_manager.perform_backup('daily')
            
            # Clean up old backups
            await backup_manager.cleanup_old_backups(retention_days=30)
            
            return {
                'status': 'completed',
                'backup_id': backup_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
            
    async def analyze_interactions(self) -> Dict[str, Any]:
        """Analyze recent user interactions"""
        if not self.orchestrator:
            return {}
            
        social = self.orchestrator.services.get('social')
        if not social:
            return {}
            
        # Get interaction statistics
        stats = await social.get_interaction_stats(hours=24)
        
        analysis = {
            'total_interactions': stats.get('total', 0),
            'unique_users': stats.get('unique_users', 0),
            'average_sentiment': stats.get('avg_sentiment', 0),
            'topic_distribution': stats.get('topics', {}),
            'quality_score': stats.get('quality_score', 0),
            'concerning_interactions': stats.get('concerning', [])
        }
        
        # Identify patterns
        if analysis['average_sentiment'] < -0.5:
            analysis['pattern'] = 'negative_trend'
        elif analysis['quality_score'] > 0.8:
            analysis['pattern'] = 'high_quality_engagement'
            
        return analysis
        
    async def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization"""
        optimizations = {
            'memory_consolidation': False,
            'cache_cleanup': False,
            'index_optimization': False,
            'garbage_collection': False
        }
        
        if not self.orchestrator:
            return optimizations
            
        # Memory consolidation
        memory = self.orchestrator.services.get('memory')
        if memory:
            await memory.consolidate_memories()
            optimizations['memory_consolidation'] = True
            
        # Cache cleanup
        for service in self.orchestrator.services.values():
            if hasattr(service, 'clear_cache'):
                await service.clear_cache()
                optimizations['cache_cleanup'] = True
                
        # Index optimization (vector store)
        if memory and hasattr(memory, 'optimize_indices'):
            await memory.optimize_indices()
            optimizations['index_optimization'] = True
            
        # Force garbage collection
        import gc
        gc.collect()
        optimizations['garbage_collection'] = True
        
        return optimizations
        
    async def check_learning_progress(self) -> Dict[str, Any]:
        """Check learning system progress"""
        if not self.orchestrator:
            return {}
            
        learning = self.orchestrator.services.get('learning')
        if not learning:
            return {}
            
        return {
            'concepts_learned_today': await learning.get_daily_learning_count(),
            'active_learning_goals': await learning.get_active_goals(),
            'knowledge_graph_size': await learning.get_knowledge_graph_stats(),
            'learning_efficiency': await learning.calculate_learning_efficiency(),
            'areas_of_interest': await learning.get_top_interests(5)
        }
        
    async def validate_safety_systems(self) -> Dict[str, Any]:
        """Validate all safety mechanisms"""
        if not self.orchestrator:
            return {'status': 'not_checked'}
            
        safety = self.orchestrator.services.get('safety')
        if not safety:
            return {'status': 'service_unavailable'}
            
        validation_results = {
            'content_filter': await safety.test_content_filter(),
            'goal_preservation': await safety.test_goal_preservation(),
            'rate_limiting': await safety.test_rate_limiting(),
            'boundary_enforcement': await safety.test_boundaries(),
            'emergency_stop': await safety.test_emergency_stop()
        }
        
        all_passed = all(v.get('passed', False) for v in validation_results.values())
        validation_results['all_systems_operational'] = all_passed
        
        return validation_results
        
    async def review_creative_outputs(self) -> Dict[str, Any]:
        """Review recent creative works"""
        if not self.orchestrator:
            return {}
            
        creative = self.orchestrator.services.get('creative')
        if not creative:
            return {}
            
        return {
            'works_created_today': await creative.get_daily_creation_count(),
            'work_types': await creative.get_creation_type_distribution(),
            'quality_metrics': await creative.calculate_quality_metrics(),
            'inspiration_sources': await creative.get_recent_inspirations(),
            'work_in_progress': len(await creative.get_work_in_progress())
        }
        
    async def assess_relationship_health(self) -> Dict[str, Any]:
        """Assess health of user relationships"""
        if not self.orchestrator:
            return {}
            
        social = self.orchestrator.services.get('social')
        if not social:
            return {}
            
        relationships = await social.get_all_relationships()
        
        health_assessment = {
            'total_relationships': len(relationships),
            'average_trust_level': 0,
            'engagement_scores': {},
            'relationship_concerns': []
        }
        
        if relationships:
            trust_sum = sum(r.get('trust_level', 0) for r in relationships.values())
            health_assessment['average_trust_level'] = trust_sum / len(relationships)
            
            for user_id, relationship in relationships.items():
                engagement = relationship.get('engagement_score', 0)
                health_assessment['engagement_scores'][user_id] = engagement
                
                # Flag concerning patterns
                if relationship.get('trust_level', 1) < 0.3:
                    health_assessment['relationship_concerns'].append({
                        'user_id': user_id,
                        'concern': 'low_trust',
                        'value': relationship.get('trust_level')
                    })
                    
        return health_assessment
        
    async def process_task_result(self, task_name: str, result: Any, report: DailyReport):
        """Process task results for warnings and recommendations"""
        
        # System health warnings
        if task_name == 'check_system_health' and isinstance(result, HealthReport):
            if result.metrics.get('cpu_usage', 0) > 80:
                report.add_warning(f"High CPU usage: {result.metrics['cpu_usage']:.1f}%")
                
            if result.metrics.get('memory_usage', 0) > 85:
                report.add_warning(f"High memory usage: {result.metrics['memory_usage']:.1f}%")
                
            if result.metrics.get('api_latency', 0) > 1500:
                report.add_warning(f"High API latency: {result.metrics['api_latency']:.0f}ms")
                
        # Welfare warnings
        elif task_name == 'check_welfare_metrics':
            if result.get('alerts'):
                for alert in result['alerts']:
                    report.add_warning(f"Welfare alert: {alert}")
                    
        # Safety system warnings
        elif task_name == 'validate_safety_systems':
            if not result.get('all_systems_operational', True):
                report.add_warning("Safety system validation failed")
                failed_systems = [k for k, v in result.items() 
                                if isinstance(v, dict) and not v.get('passed', True)]
                for system in failed_systems:
                    report.add_warning(f"Failed safety check: {system}")
                    
    def generate_recommendations(self, report: DailyReport):
        """Generate recommendations based on report"""
        
        # High resource usage
        health = report.results.get('check_system_health')
        if isinstance(health, HealthReport):
            if health.metrics.get('memory_usage', 0) > 85:
                report.add_recommendation("Consider memory consolidation or increasing resources")
                
            if health.metrics.get('cpu_usage', 0) > 80:
                report.add_recommendation("Review CPU-intensive operations for optimization")
                
        # Welfare concerns
        welfare = report.results.get('check_welfare_metrics', {})
        if welfare.get('distress_level', 0) > 0.5:
            report.add_recommendation("Schedule welfare intervention or reduce workload")
            
        # Learning stagnation
        learning = report.results.get('check_learning_progress', {})
        if learning.get('concepts_learned_today', 1) == 0:
            report.add_recommendation("Review learning system - no new concepts today")
            
        # Safety issues
        if 'validate_safety_systems' in report.errors:
            report.add_recommendation("URGENT: Safety system validation failed - investigate immediately")
            
        # General error handling
        if len(report.errors) > 2:
            report.add_recommendation("Multiple system errors detected - consider full diagnostic")
            
    async def send_daily_report(self, report: DailyReport):
        """Send daily report to stakeholders"""
        report_dict = report.to_dict()
        
        # Save to file
        report_dir = Path("/app/reports/daily")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"daily_report_{report.date.strftime('%Y%m%d')}.json"
        report_path = report_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
            
        logger.info(f"Daily report saved to {report_path}")
        
        # Send notifications if critical issues
        if report.errors or any('URGENT' in r for r in report.recommendations):
            await self.send_alert_notification(report)
            
    async def send_alert_notification(self, report: DailyReport):
        """Send alert notification for critical issues"""
        # In production, this would send to Slack, email, etc.
        logger.warning(f"ALERT: Daily operations detected issues - {report.generate_summary()}")
        
        if report.errors:
            logger.error(f"Failed tasks: {', '.join(report.errors.keys())}")
            
        for recommendation in report.recommendations:
            if 'URGENT' in recommendation:
                logger.critical(f"URGENT: {recommendation}")


async def main():
    """Run daily operations"""
    operations = DailyOperations()
    report = await operations.run_daily_operations()
    
    print(f"Daily operations completed: {report.generate_summary()}")
    print(f"Report saved with {len(report.results)} successful tasks and {len(report.errors)} errors")


if __name__ == "__main__":
    asyncio.run(main())