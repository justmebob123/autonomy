"""
Message Analytics for the Message Bus System

Provides analytics, pattern detection, and performance metrics for messages.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from .message import Message, MessageType, MessagePriority


class MessageAnalytics:
    """
    Analytics engine for message bus.
    
    Provides:
    - Frequency analysis
    - Pattern detection
    - Performance metrics
    - Trend analysis
    """
    
    def __init__(self, message_bus):
        """
        Initialize analytics engine.
        
        Args:
            message_bus: MessageBus instance to analyze
        """
        self.message_bus = message_bus
    
    def get_frequency_analysis(self, time_window: Optional[timedelta] = None) -> Dict:
        """
        Analyze message frequency.
        
        Args:
            time_window: Time window to analyze (None = all time)
        
        Returns:
            Dict with frequency metrics
        """
        since = datetime.now() - time_window if time_window else None
        messages = self.message_bus.search_messages(since=since)
        
        if not messages:
            return {
                'total_messages': 0,
                'messages_per_hour': 0,
                'by_type': {},
                'by_sender': {},
                'by_priority': {},
            }
        
        # Calculate time span
        if len(messages) > 1:
            time_span = (messages[0].timestamp - messages[-1].timestamp).total_seconds() / 3600
        else:
            time_span = 1
        
        # Count by type
        by_type = Counter(msg.message_type for msg in messages)
        
        # Count by sender
        by_sender = Counter(msg.sender for msg in messages)
        
        # Count by priority
        by_priority = Counter(msg.priority for msg in messages)
        
        return {
            'total_messages': len(messages),
            'messages_per_hour': len(messages) / max(time_span, 1),
            'time_span_hours': time_span,
            'by_type': {k.value: v for k, v in by_type.most_common()},
            'by_sender': dict(by_sender.most_common()),
            'by_priority': {k.name: v for k, v in by_priority.most_common()},
        }
    
    def detect_patterns(self, time_window: timedelta = timedelta(hours=1)) -> Dict:
        """
        Detect patterns in message flow.
        
        Args:
            time_window: Time window to analyze
        
        Returns:
            Dict with detected patterns
        """
        since = datetime.now() - time_window
        messages = self.message_bus.search_messages(since=since)
        
        patterns = {
            'repeated_errors': [],
            'message_bursts': [],
            'slow_responses': [],
            'common_sequences': [],
        }
        
        if not messages:
            return patterns
        
        # Detect repeated errors (same error type from same sender)
        error_messages = [m for m in messages if 'error' in m.message_type.value.lower()]
        error_groups = defaultdict(list)
        for msg in error_messages:
            key = (msg.sender, msg.message_type)
            error_groups[key].append(msg)
        
        for (sender, msg_type), msgs in error_groups.items():
            if len(msgs) >= 3:
                patterns['repeated_errors'].append({
                    'sender': sender,
                    'type': msg_type.value,
                    'count': len(msgs),
                    'first_occurrence': msgs[-1].timestamp.isoformat(),
                    'last_occurrence': msgs[0].timestamp.isoformat(),
                })
        
        # Detect message bursts (many messages in short time)
        if len(messages) > 10:
            # Group messages by 5-minute windows
            time_buckets = defaultdict(int)
            for msg in messages:
                bucket = msg.timestamp.replace(second=0, microsecond=0)
                bucket = bucket.replace(minute=(bucket.minute // 5) * 5)
                time_buckets[bucket] += 1
            
            # Find bursts (>10 messages in 5 minutes)
            for bucket, count in time_buckets.items():
                if count > 10:
                    patterns['message_bursts'].append({
                        'time': bucket.isoformat(),
                        'count': count,
                        'rate_per_minute': count / 5,
                    })
        
        # Detect slow responses (request-response pairs with long delays)
        request_messages = [m for m in messages if m.requires_response]
        for req in request_messages:
            responses = [m for m in messages if m.in_response_to == req.id]
            if responses:
                response = responses[0]
                delay = (response.timestamp - req.timestamp).total_seconds()
                if delay > 30:  # Slow if >30 seconds
                    patterns['slow_responses'].append({
                        'request_id': req.id,
                        'sender': req.sender,
                        'recipient': req.recipient,
                        'delay_seconds': delay,
                    })
        
        # Detect common message sequences
        if len(messages) >= 3:
            sequences = []
            for i in range(len(messages) - 2):
                seq = tuple(m.message_type for m in messages[i:i+3])
                sequences.append(seq)
            
            seq_counts = Counter(sequences)
            for seq, count in seq_counts.most_common(5):
                if count >= 2:
                    patterns['common_sequences'].append({
                        'sequence': [t.value for t in seq],
                        'count': count,
                    })
        
        return patterns
    
    def get_performance_metrics(self, time_window: Optional[timedelta] = None) -> Dict:
        """
        Calculate performance metrics.
        
        Args:
            time_window: Time window to analyze
        
        Returns:
            Dict with performance metrics
        """
        since = datetime.now() - time_window if time_window else None
        messages = self.message_bus.search_messages(since=since)
        
        if not messages:
            return {
                'total_messages': 0,
                'avg_delivery_time': 0,
                'critical_message_ratio': 0,
                'response_times': {},
            }
        
        # Calculate critical message ratio
        critical_count = sum(1 for m in messages if m.priority == MessagePriority.CRITICAL)
        critical_ratio = critical_count / len(messages) if messages else 0
        
        # Calculate response times for request-response pairs
        response_times = []
        request_messages = [m for m in messages if m.requires_response]
        for req in request_messages:
            responses = [m for m in messages if m.in_response_to == req.id]
            if responses:
                response = responses[0]
                delay = (response.timestamp - req.timestamp).total_seconds()
                response_times.append(delay)
        
        response_stats = {}
        if response_times:
            response_stats = {
                'count': len(response_times),
                'avg': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'stdev': statistics.stdev(response_times) if len(response_times) > 1 else 0,
            }
        
        # Calculate message processing rate
        if len(messages) > 1:
            time_span = (messages[0].timestamp - messages[-1].timestamp).total_seconds()
            processing_rate = len(messages) / max(time_span, 1)
        else:
            processing_rate = 0
        
        return {
            'total_messages': len(messages),
            'processing_rate': processing_rate,
            'critical_message_ratio': critical_ratio,
            'critical_message_count': critical_count,
            'response_times': response_stats,
            'message_types_count': len(set(m.message_type for m in messages)),
            'unique_senders': len(set(m.sender for m in messages)),
            'unique_recipients': len(set(m.recipient for m in messages)),
        }
    
    def get_trend_analysis(self, time_windows: List[timedelta]) -> Dict:
        """
        Analyze trends over multiple time windows.
        
        Args:
            time_windows: List of time windows to compare
        
        Returns:
            Dict with trend analysis
        """
        trends = {
            'message_volume': [],
            'critical_ratio': [],
            'error_rate': [],
            'response_time': [],
        }
        
        for window in time_windows:
            since = datetime.now() - window
            messages = self.message_bus.search_messages(since=since)
            
            if messages:
                # Message volume
                trends['message_volume'].append({
                    'window': str(window),
                    'count': len(messages),
                })
                
                # Critical ratio
                critical_count = sum(1 for m in messages if m.priority == MessagePriority.CRITICAL)
                trends['critical_ratio'].append({
                    'window': str(window),
                    'ratio': critical_count / len(messages),
                })
                
                # Error rate
                error_count = sum(1 for m in messages if 'error' in m.message_type.value.lower())
                trends['error_rate'].append({
                    'window': str(window),
                    'ratio': error_count / len(messages),
                })
                
                # Response time
                request_messages = [m for m in messages if m.requires_response]
                response_times = []
                for req in request_messages:
                    responses = [m for m in messages if m.in_response_to == req.id]
                    if responses:
                        delay = (responses[0].timestamp - req.timestamp).total_seconds()
                        response_times.append(delay)
                
                if response_times:
                    trends['response_time'].append({
                        'window': str(window),
                        'avg': statistics.mean(response_times),
                    })
        
        return trends
    
    def get_phase_communication_matrix(self) -> Dict:
        """
        Generate communication matrix between phases.
        
        Returns:
            Dict with phase-to-phase communication counts
        """
        messages = self.message_bus.message_history
        
        matrix = defaultdict(lambda: defaultdict(int))
        
        for msg in messages:
            if msg.sender and msg.recipient and msg.recipient != "broadcast":
                matrix[msg.sender][msg.recipient] += 1
        
        return {
            'matrix': {sender: dict(recipients) for sender, recipients in matrix.items()},
            'total_direct_messages': sum(sum(r.values()) for r in matrix.values()),
        }
    
    def get_objective_message_analysis(self) -> Dict:
        """
        Analyze messages by objective.
        
        Returns:
            Dict with objective-level message analysis
        """
        messages = self.message_bus.message_history
        
        by_objective = defaultdict(lambda: {
            'total': 0,
            'by_type': Counter(),
            'critical_count': 0,
        })
        
        for msg in messages:
            if msg.objective_id:
                obj_data = by_objective[msg.objective_id]
                obj_data['total'] += 1
                obj_data['by_type'][msg.message_type] += 1
                if msg.priority == MessagePriority.CRITICAL:
                    obj_data['critical_count'] += 1
        
        return {
            objective_id: {
                'total': data['total'],
                'by_type': {k.value: v for k, v in data['by_type'].most_common()},
                'critical_count': data['critical_count'],
            }
            for objective_id, data in by_objective.items()
        }
    
    def generate_report(self, time_window: timedelta = timedelta(hours=24)) -> str:
        """
        Generate comprehensive analytics report.
        
        Args:
            time_window: Time window for analysis
        
        Returns:
            Formatted report string
        """
        freq = self.get_frequency_analysis(time_window)
        patterns = self.detect_patterns(time_window)
        perf = self.get_performance_metrics(time_window)
        
        report = []
        report.append("=" * 60)
        report.append("MESSAGE BUS ANALYTICS REPORT")
        report.append("=" * 60)
        report.append(f"Time Window: {time_window}")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Frequency Analysis
        report.append("FREQUENCY ANALYSIS")
        report.append("-" * 60)
        report.append(f"Total Messages: {freq['total_messages']}")
        report.append(f"Messages/Hour: {freq['messages_per_hour']:.2f}")
        report.append(f"Time Span: {freq['time_span_hours']:.2f} hours")
        report.append("")
        
        report.append("Top Message Types:")
        for msg_type, count in list(freq['by_type'].items())[:5]:
            report.append(f"  {msg_type}: {count}")
        report.append("")
        
        report.append("Top Senders:")
        for sender, count in list(freq['by_sender'].items())[:5]:
            report.append(f"  {sender}: {count}")
        report.append("")
        
        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 60)
        report.append(f"Processing Rate: {perf['processing_rate']:.2f} msg/sec")
        report.append(f"Critical Message Ratio: {perf['critical_message_ratio']:.2%}")
        report.append(f"Unique Senders: {perf['unique_senders']}")
        report.append(f"Unique Recipients: {perf['unique_recipients']}")
        
        if perf['response_times']:
            report.append("")
            report.append("Response Times:")
            rt = perf['response_times']
            report.append(f"  Count: {rt['count']}")
            report.append(f"  Average: {rt['avg']:.2f}s")
            report.append(f"  Median: {rt['median']:.2f}s")
            report.append(f"  Min: {rt['min']:.2f}s")
            report.append(f"  Max: {rt['max']:.2f}s")
        report.append("")
        
        # Pattern Detection
        report.append("PATTERN DETECTION")
        report.append("-" * 60)
        
        if patterns['repeated_errors']:
            report.append("Repeated Errors:")
            for error in patterns['repeated_errors'][:3]:
                report.append(f"  {error['sender']}: {error['type']} ({error['count']} times)")
        
        if patterns['message_bursts']:
            report.append("")
            report.append("Message Bursts:")
            for burst in patterns['message_bursts'][:3]:
                report.append(f"  {burst['time']}: {burst['count']} messages ({burst['rate_per_minute']:.1f}/min)")
        
        if patterns['slow_responses']:
            report.append("")
            report.append("Slow Responses:")
            for slow in patterns['slow_responses'][:3]:
                report.append(f"  {slow['sender']} → {slow['recipient']}: {slow['delay_seconds']:.1f}s")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)