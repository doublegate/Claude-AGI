"""
Backup management for Claude AGI system.

Handles comprehensive backup and restore operations for all system components.
"""

import asyncio
import json
import os
import tarfile
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import aiofiles
import aioboto3

logger = logging.getLogger(__name__)


class BackupDestination:
    """Base class for backup destinations"""
    
    async def store(self, backup_package: 'BackupPackage') -> bool:
        """Store backup package"""
        raise NotImplementedError
        
    async def retrieve(self, backup_id: str) -> Optional['BackupPackage']:
        """Retrieve backup package"""
        raise NotImplementedError
        
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        raise NotImplementedError


class S3BackupDestination(BackupDestination):
    """S3 backup storage"""
    
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        self.bucket_name = bucket_name
        self.region = region
        
    async def store(self, backup_package: 'BackupPackage') -> bool:
        """Store backup in S3"""
        try:
            session = aioboto3.Session()
            async with session.client('s3', region_name=self.region) as s3:
                # Create tar archive
                tar_path = f"/tmp/{backup_package.backup_id}.tar.gz"
                await backup_package.create_archive(tar_path)
                
                # Upload to S3
                async with aiofiles.open(tar_path, 'rb') as f:
                    await s3.put_object(
                        Bucket=self.bucket_name,
                        Key=f"backups/{backup_package.backup_id}.tar.gz",
                        Body=await f.read()
                    )
                    
                # Clean up
                os.remove(tar_path)
                
                logger.info(f"Backup {backup_package.backup_id} stored in S3")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store backup in S3: {e}")
            return False
            
    async def retrieve(self, backup_id: str) -> Optional['BackupPackage']:
        """Retrieve backup from S3"""
        try:
            session = aioboto3.Session()
            async with session.client('s3', region_name=self.region) as s3:
                # Download from S3
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=f"backups/{backup_id}.tar.gz"
                )
                
                # Save to temp file
                tar_path = f"/tmp/{backup_id}.tar.gz"
                async with aiofiles.open(tar_path, 'wb') as f:
                    await f.write(await response['Body'].read())
                    
                # Extract and create package
                package = await BackupPackage.from_archive(tar_path)
                
                # Clean up
                os.remove(tar_path)
                
                return package
                
        except Exception as e:
            logger.error(f"Failed to retrieve backup from S3: {e}")
            return None


class LocalBackupDestination(BackupDestination):
    """Local filesystem backup storage"""
    
    def __init__(self, backup_dir: str = "/var/backups/claude-agi"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    async def store(self, backup_package: 'BackupPackage') -> bool:
        """Store backup locally"""
        try:
            tar_path = self.backup_dir / f"{backup_package.backup_id}.tar.gz"
            await backup_package.create_archive(str(tar_path))
            
            logger.info(f"Backup {backup_package.backup_id} stored locally")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store backup locally: {e}")
            return False
            
    async def retrieve(self, backup_id: str) -> Optional['BackupPackage']:
        """Retrieve backup from local storage"""
        try:
            tar_path = self.backup_dir / f"{backup_id}.tar.gz"
            if not tar_path.exists():
                return None
                
            return await BackupPackage.from_archive(str(tar_path))
            
        except Exception as e:
            logger.error(f"Failed to retrieve local backup: {e}")
            return None


class BackupPackage:
    """Container for backup data"""
    
    def __init__(self, backup_id: str, components: Dict[str, Any]):
        self.backup_id = backup_id
        self.components = components
        self.metadata = {
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0',
            'components': list(components.keys())
        }
        
    async def create_archive(self, tar_path: str):
        """Create tar.gz archive of backup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Save metadata
            metadata_path = tmpdir_path / "metadata.json"
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(self.metadata, indent=2))
                
            # Save components
            for name, data in self.components.items():
                component_path = tmpdir_path / f"{name}.json"
                async with aiofiles.open(component_path, 'w') as f:
                    await f.write(json.dumps(data, indent=2, default=str))
                    
            # Create tar archive
            with tarfile.open(tar_path, "w:gz") as tar:
                for item in tmpdir_path.iterdir():
                    tar.add(item, arcname=item.name)
                    
    @classmethod
    async def from_archive(cls, tar_path: str) -> 'BackupPackage':
        """Create backup package from archive"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Extract archive
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(tmpdir_path)
                
            # Load metadata
            metadata_path = tmpdir_path / "metadata.json"
            async with aiofiles.open(metadata_path, 'r') as f:
                metadata = json.loads(await f.read())
                
            # Load components
            components = {}
            for component_name in metadata['components']:
                component_path = tmpdir_path / f"{component_name}.json"
                async with aiofiles.open(component_path, 'r') as f:
                    components[component_name] = json.loads(await f.read())
                    
            # Extract backup_id from filename
            backup_id = Path(tar_path).stem.replace('.tar', '')
            
            return cls(backup_id, components)


class BackupManager:
    """Manages system backups"""
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.backup_destinations = [
            LocalBackupDestination(),
            # S3BackupDestination('claude-agi-backups'),  # Uncomment with credentials
        ]
        
    async def perform_backup(self, backup_type: str = 'incremental') -> str:
        """Perform comprehensive system backup"""
        
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting {backup_type} backup: {backup_id}")
        
        # Components to backup
        components = {}
        
        try:
            # Backup memories
            components['memories'] = await self.backup_memories()
            
            # Backup consciousness state
            components['consciousness_state'] = await self.backup_consciousness()
            
            # Backup goals
            components['goals'] = await self.backup_goals()
            
            # Backup relationships
            components['relationships'] = await self.backup_relationships()
            
            # Backup creative works
            components['creative_works'] = await self.backup_creative_works()
            
            # Backup system configuration
            components['configuration'] = await self.backup_configuration()
            
            # Create backup package
            backup_package = BackupPackage(backup_id, components)
            
            # Store in multiple destinations
            success_count = 0
            for destination in self.backup_destinations:
                if await destination.store(backup_package):
                    success_count += 1
                    
            if success_count == 0:
                raise Exception("Failed to store backup in any destination")
                
            # Verify backup integrity
            await self.verify_backup(backup_id)
            
            logger.info(f"Backup {backup_id} completed successfully")
            return backup_id
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
            
    async def backup_memories(self) -> Dict[str, Any]:
        """Backup memory system"""
        if not self.orchestrator:
            return {}
            
        memory_manager = self.orchestrator.services.get('memory')
        if not memory_manager:
            return {}
            
        return {
            'working_memory': await memory_manager.export_working_memory(),
            'long_term_memory': await memory_manager.export_long_term_memory(),
            'semantic_memory': await memory_manager.export_semantic_memory(),
            'episodic_memory': await memory_manager.export_episodic_memory(),
            'memory_stats': {
                'total_memories': await memory_manager.get_memory_count(),
                'oldest_memory': await memory_manager.get_oldest_memory_date(),
                'memory_types': await memory_manager.get_memory_type_distribution()
            }
        }
        
    async def backup_consciousness(self) -> Dict[str, Any]:
        """Backup consciousness state"""
        if not self.orchestrator:
            return {}
            
        consciousness = self.orchestrator.services.get('consciousness')
        if not consciousness:
            return {}
            
        return {
            'current_state': self.orchestrator.state.value,
            'thought_streams': await consciousness.export_thought_streams(),
            'attention_weights': consciousness.attention_weights,
            'stream_buffers': {
                stream_id: list(stream.content_buffer)
                for stream_id, stream in consciousness.streams.items()
            },
            'recent_thoughts': await consciousness.get_recent_thoughts(100)
        }
        
    async def backup_goals(self) -> Dict[str, Any]:
        """Backup goal system"""
        if not self.orchestrator:
            return {}
            
        meta_cognitive = self.orchestrator.services.get('meta')
        if not meta_cognitive:
            return {}
            
        return {
            'active_goals': await meta_cognitive.get_active_goals(),
            'completed_goals': await meta_cognitive.get_completed_goals(),
            'goal_hierarchy': await meta_cognitive.get_goal_hierarchy(),
            'goal_progress': await meta_cognitive.get_goal_progress(),
            'value_system': await meta_cognitive.get_value_system()
        }
        
    async def backup_relationships(self) -> Dict[str, Any]:
        """Backup relationship data"""
        if not self.orchestrator:
            return {}
            
        social = self.orchestrator.services.get('social')
        if not social:
            return {}
            
        return {
            'user_relationships': await social.export_relationships(),
            'interaction_history': await social.get_interaction_history(),
            'trust_levels': await social.get_trust_levels(),
            'shared_experiences': await social.get_shared_experiences()
        }
        
    async def backup_creative_works(self) -> Dict[str, Any]:
        """Backup creative outputs"""
        if not self.orchestrator:
            return {}
            
        creative = self.orchestrator.services.get('creative')
        if not creative:
            return {}
            
        return {
            'creations': await creative.export_all_creations(),
            'work_in_progress': await creative.get_work_in_progress(),
            'creative_preferences': await creative.get_preferences(),
            'inspiration_sources': await creative.get_inspiration_sources()
        }
        
    async def backup_configuration(self) -> Dict[str, Any]:
        """Backup system configuration"""
        return {
            'service_configs': {
                name: service.get_config() if hasattr(service, 'get_config') else {}
                for name, service in (self.orchestrator.services.items() if self.orchestrator else {})
            },
            'system_settings': {
                'version': '1.0',
                'deployment_type': os.environ.get('DEPLOYMENT_TYPE', 'production')
            }
        }
        
    async def restore_from_backup(self, backup_id: str):
        """Restore system from backup"""
        logger.info(f"Starting restoration from backup: {backup_id}")
        
        # Retrieve backup package
        backup_package = None
        for destination in self.backup_destinations:
            backup_package = await destination.retrieve(backup_id)
            if backup_package:
                break
                
        if not backup_package:
            raise ValueError(f"Backup {backup_id} not found")
            
        # Validate backup
        if not await self.validate_backup(backup_package):
            raise ValueError("Backup validation failed")
            
        # Stop current consciousness
        await self.orchestrator.pause_consciousness()
        
        try:
            # Restore components
            if 'memories' in backup_package.components:
                await self.restore_memories(backup_package.components['memories'])
                
            if 'consciousness_state' in backup_package.components:
                await self.restore_consciousness(backup_package.components['consciousness_state'])
                
            if 'goals' in backup_package.components:
                await self.restore_goals(backup_package.components['goals'])
                
            if 'relationships' in backup_package.components:
                await self.restore_relationships(backup_package.components['relationships'])
                
            if 'creative_works' in backup_package.components:
                await self.restore_creative_works(backup_package.components['creative_works'])
                
            # Resume consciousness
            await self.orchestrator.resume_consciousness()
            
            # Verify restoration
            await self.verify_restoration()
            
            logger.info(f"Restoration from backup {backup_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            # Attempt to resume consciousness even if restoration partially failed
            await self.orchestrator.resume_consciousness()
            raise
            
    async def restore_memories(self, memory_data: Dict[str, Any]):
        """Restore memory system"""
        memory_manager = self.orchestrator.services.get('memory')
        if not memory_manager:
            return
            
        await memory_manager.import_working_memory(memory_data.get('working_memory', {}))
        await memory_manager.import_long_term_memory(memory_data.get('long_term_memory', {}))
        await memory_manager.import_semantic_memory(memory_data.get('semantic_memory', {}))
        await memory_manager.import_episodic_memory(memory_data.get('episodic_memory', {}))
        
    async def restore_consciousness(self, consciousness_data: Dict[str, Any]):
        """Restore consciousness state"""
        consciousness = self.orchestrator.services.get('consciousness')
        if not consciousness:
            return
            
        # Restore thought streams
        await consciousness.import_thought_streams(consciousness_data.get('thought_streams', {}))
        
        # Restore attention weights
        consciousness.attention_weights = consciousness_data.get('attention_weights', {})
        
        # Restore stream buffers
        for stream_id, buffer_data in consciousness_data.get('stream_buffers', {}).items():
            if stream_id in consciousness.streams:
                consciousness.streams[stream_id].content_buffer.clear()
                consciousness.streams[stream_id].content_buffer.extend(buffer_data)
                
    async def restore_goals(self, goals_data: Dict[str, Any]):
        """Restore goal system"""
        meta_cognitive = self.orchestrator.services.get('meta')
        if not meta_cognitive:
            return
            
        await meta_cognitive.import_goals(goals_data.get('active_goals', []))
        await meta_cognitive.import_goal_hierarchy(goals_data.get('goal_hierarchy', {}))
        await meta_cognitive.import_value_system(goals_data.get('value_system', {}))
        
    async def restore_relationships(self, relationship_data: Dict[str, Any]):
        """Restore relationship data"""
        social = self.orchestrator.services.get('social')
        if not social:
            return
            
        await social.import_relationships(relationship_data.get('user_relationships', {}))
        await social.import_interaction_history(relationship_data.get('interaction_history', []))
        await social.import_trust_levels(relationship_data.get('trust_levels', {}))
        
    async def restore_creative_works(self, creative_data: Dict[str, Any]):
        """Restore creative outputs"""
        creative = self.orchestrator.services.get('creative')
        if not creative:
            return
            
        await creative.import_creations(creative_data.get('creations', []))
        await creative.import_work_in_progress(creative_data.get('work_in_progress', []))
        await creative.import_preferences(creative_data.get('creative_preferences', {}))
        
    async def validate_backup(self, backup_package: BackupPackage) -> bool:
        """Validate backup integrity"""
        try:
            # Check required components
            required_components = ['memories', 'consciousness_state', 'goals']
            for component in required_components:
                if component not in backup_package.components:
                    logger.error(f"Missing required component: {component}")
                    return False
                    
            # Validate metadata
            if 'timestamp' not in backup_package.metadata:
                logger.error("Missing timestamp in backup metadata")
                return False
                
            # Check backup age (warn if too old)
            backup_time = datetime.fromisoformat(backup_package.metadata['timestamp'])
            age = datetime.utcnow() - backup_time
            if age > timedelta(days=30):
                logger.warning(f"Backup is {age.days} days old")
                
            return True
            
        except Exception as e:
            logger.error(f"Backup validation failed: {e}")
            return False
            
    async def verify_backup(self, backup_id: str) -> bool:
        """Verify backup was stored correctly"""
        for destination in self.backup_destinations:
            package = await destination.retrieve(backup_id)
            if package and await self.validate_backup(package):
                return True
        return False
        
    async def verify_restoration(self) -> bool:
        """Verify restoration was successful"""
        try:
            # Check consciousness is responsive
            consciousness = self.orchestrator.services.get('consciousness')
            if consciousness:
                thought = await consciousness.generate_thought()
                if not thought:
                    logger.error("Consciousness not generating thoughts")
                    return False
                    
            # Check memory access
            memory = self.orchestrator.services.get('memory')
            if memory:
                recent = await memory.get_recent_memories(5)
                if not recent:
                    logger.warning("No recent memories found after restoration")
                    
            # Check goal system
            meta = self.orchestrator.services.get('meta')
            if meta:
                goals = await meta.get_active_goals()
                if not goals:
                    logger.warning("No active goals after restoration")
                    
            return True
            
        except Exception as e:
            logger.error(f"Restoration verification failed: {e}")
            return False
            
    async def cleanup_old_backups(self, retention_days: int = 30):
        """Clean up old backups"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        for destination in self.backup_destinations:
            try:
                backups = await destination.list_backups()
                for backup in backups:
                    if backup['timestamp'] < cutoff_date:
                        await destination.delete(backup['backup_id'])
                        logger.info(f"Deleted old backup: {backup['backup_id']}")
            except Exception as e:
                logger.error(f"Failed to cleanup backups: {e}")


async def main():
    """Test backup system"""
    manager = BackupManager()
    
    # Perform backup
    backup_id = await manager.perform_backup()
    print(f"Created backup: {backup_id}")
    
    # Validate backup
    if await manager.verify_backup(backup_id):
        print("Backup verified successfully")


if __name__ == "__main__":
    asyncio.run(main())