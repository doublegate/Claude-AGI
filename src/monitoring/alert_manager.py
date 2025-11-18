"""
Alert Management System for Claude-AGI
=======================================

Comprehensive alert management including:
- Rule-based alerting
- Multiple alert channels (email, webhook, log)
- Alert severity levels
- Alert grouping and deduplication
- Alert history and tracking
"""

import logging
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SILENCED = "silenced"


@dataclass
class Alert:
    """An alert instance"""
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    count: int = 1  # For deduplication


@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    name: str
    description: str
    condition: Callable[[], bool]
    severity: AlertSeverity
    labels: Dict[str, str] = field(default_factory=dict)
    threshold: float = 0.0
    duration: int = 60  # seconds
    enabled: bool = True
    last_evaluated: Optional[datetime] = None
    last_triggered: Optional[datetime] = None


class AlertChannel:
    """Base class for alert channels"""

    async def send_alert(self, alert: Alert):
        """Send alert through this channel"""
        raise NotImplementedError


class LogChannel(AlertChannel):
    """Log-based alert channel"""

    async def send_alert(self, alert: Alert):
        """Log the alert"""
        log_method = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(alert.severity, logger.info)

        log_method(f"ALERT [{alert.severity.value.upper()}] {alert.name}: {alert.description}")


class WebhookChannel(AlertChannel):
    """Webhook-based alert channel"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_alert(self, alert: Alert):
        """Send alert via webhook"""
        payload = {
            'alert_id': alert.alert_id,
            'name': alert.name,
            'description': alert.description,
            'severity': alert.severity.value,
            'status': alert.status.value,
            'labels': alert.labels,
            'created_at': alert.created_at.isoformat()
        }

        logger.info(f"Webhook alert: {self.webhook_url} - {alert.name}")
        # In production: async with aiohttp.ClientSession() as session:
        #     await session.post(self.webhook_url, json=payload)


class EmailChannel(AlertChannel):
    """Email-based alert channel"""

    def __init__(self, smtp_config: Dict[str, str], recipients: List[str]):
        self.smtp_config = smtp_config
        self.recipients = recipients

    async def send_alert(self, alert: Alert):
        """Send alert via email"""
        subject = f"[{alert.severity.value.upper()}] {alert.name}"
        body = f"""
Alert: {alert.name}
Severity: {alert.severity.value}
Description: {alert.description}
Created: {alert.created_at}

Labels: {alert.labels}
"""

        logger.info(f"Email alert sent to {self.recipients}: {alert.name}")
        # In production: use aiosmtplib to send email


class AlertManager:
    """Central alert management system"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.channels: List[AlertChannel] = [LogChannel()]  # Default to logging
        self.silence_rules: Dict[str, datetime] = {}  # label_pattern -> until_time
        self.dedupe_window = timedelta(minutes=5)
        self.evaluation_interval = 60  # seconds
        self._evaluation_task: Optional[asyncio.Task] = None

    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Alert rule added: {rule.name}")

    def remove_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Alert rule removed: {rule_id}")

    def add_channel(self, channel: AlertChannel):
        """Add an alert channel"""
        self.channels.append(channel)
        logger.info(f"Alert channel added: {type(channel).__name__}")

    async def fire_alert(
        self,
        name: str,
        description: str,
        severity: AlertSeverity,
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None
    ) -> Alert:
        """Manually fire an alert"""

        # Check for duplicate alerts
        alert_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted((labels or {}).items()))}"

        # Deduplicate recent alerts
        for active_alert in self.active_alerts.values():
            if active_alert.name == name and active_alert.labels == (labels or {}):
                # Update existing alert
                active_alert.count += 1
                active_alert.updated_at = datetime.now()
                logger.debug(f"Alert updated (count={active_alert.count}): {name}")
                return active_alert

        # Create new alert
        alert = Alert(
            alert_id=f"alert_{datetime.now().timestamp()}_{len(self.active_alerts)}",
            name=name,
            description=description,
            severity=severity,
            labels=labels or {},
            annotations=annotations or {}
        )

        # Check if silenced
        if self._is_silenced(alert):
            alert.status = AlertStatus.SILENCED
            logger.debug(f"Alert silenced: {name}")
            return alert

        # Store alert
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)

        # Send through channels
        await self._send_to_channels(alert)

        logger.info(f"Alert fired: {name} [{severity.value}]")

        return alert

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.updated_at = datetime.now()
            logger.info(f"Alert acknowledged by {acknowledged_by}: {alert.name}")

    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            alert.updated_at = datetime.now()

            # Remove from active alerts
            del self.active_alerts[alert_id]

            logger.info(f"Alert resolved: {alert.name}")

    def silence_alerts(
        self,
        label_pattern: Dict[str, str],
        duration: timedelta
    ):
        """Silence alerts matching label pattern"""
        pattern_key = ':'.join(f'{k}={v}' for k, v in sorted(label_pattern.items()))
        self.silence_rules[pattern_key] = datetime.now() + duration

        logger.info(f"Alerts silenced for {duration}: {pattern_key}")

    async def evaluate_rules(self):
        """Evaluate all alert rules"""
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            try:
                # Evaluate condition
                triggered = rule.condition()

                rule.last_evaluated = datetime.now()

                if triggered:
                    # Check if duration threshold met
                    if rule.last_triggered:
                        time_since_trigger = datetime.now() - rule.last_triggered
                        if time_since_trigger.total_seconds() < rule.duration:
                            continue

                    # Fire alert
                    await self.fire_alert(
                        name=rule.name,
                        description=rule.description,
                        severity=rule.severity,
                        labels=rule.labels
                    )

                    rule.last_triggered = datetime.now()

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")

    async def start_evaluation_loop(self):
        """Start continuous rule evaluation"""
        logger.info(f"Starting alert evaluation loop (interval={self.evaluation_interval}s)")

        async def evaluation_loop():
            while True:
                try:
                    await self.evaluate_rules()
                    await asyncio.sleep(self.evaluation_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in evaluation loop: {e}")
                    await asyncio.sleep(self.evaluation_interval)

        self._evaluation_task = asyncio.create_task(evaluation_loop())

    async def stop_evaluation_loop(self):
        """Stop rule evaluation"""
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass

            logger.info("Alert evaluation loop stopped")

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[Alert]:
        """Get active alerts with optional filtering"""
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if labels:
            alerts = [
                a for a in alerts
                if all(a.labels.get(k) == v for k, v in labels.items())
            ]

        return alerts

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)

        severity_counts = defaultdict(int)
        for alert in self.alert_history:
            severity_counts[alert.severity.value] += 1

        # Calculate MTTR (Mean Time To Resolve)
        resolved_alerts = [
            a for a in self.alert_history
            if a.resolved_at and a.created_at
        ]

        if resolved_alerts:
            resolution_times = [
                (a.resolved_at - a.created_at).total_seconds()
                for a in resolved_alerts
            ]
            mttr = sum(resolution_times) / len(resolution_times)
        else:
            mttr = 0

        return {
            'total_alerts': total_alerts,
            'active_alerts': active_count,
            'resolved_alerts': len(resolved_alerts),
            'severity_distribution': dict(severity_counts),
            'mean_time_to_resolve_seconds': mttr,
            'alert_rate_per_hour': total_alerts / max((datetime.now() - self.alert_history[0].created_at).total_seconds() / 3600, 1) if total_alerts > 0 else 0
        }

    async def _send_to_channels(self, alert: Alert):
        """Send alert to all configured channels"""
        tasks = [channel.send_alert(alert) for channel in self.channels]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _is_silenced(self, alert: Alert) -> bool:
        """Check if alert matches any silence rules"""
        now = datetime.now()

        # Clean expired silence rules
        expired = [k for k, v in self.silence_rules.items() if now > v]
        for k in expired:
            del self.silence_rules[k]

        # Check if alert matches any active silence rule
        for pattern_key, until_time in self.silence_rules.items():
            if now < until_time:
                # Simple matching - could be enhanced with regex
                pattern_labels = dict(item.split('=') for item in pattern_key.split(':'))
                if all(alert.labels.get(k) == v for k, v in pattern_labels.items()):
                    return True

        return False

    def clear_history(self, older_than: Optional[timedelta] = None):
        """Clear alert history"""
        if older_than:
            cutoff = datetime.now() - older_than
            self.alert_history = [
                a for a in self.alert_history
                if a.created_at > cutoff
            ]
        else:
            self.alert_history.clear()

        logger.info("Alert history cleared")


# Global alert manager instance
_alert_manager = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
