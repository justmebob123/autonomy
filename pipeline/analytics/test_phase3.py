#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 3: Advanced Analytics

Tests:
- Predictive Analytics Engine
- Anomaly Detection System
- Optimization Recommendations Engine
"""

import unittest
from datetime import datetime, timedelta
from predictive_engine import (
    PredictiveAnalyticsEngine,
    PhasePrediction,
    TaskPrediction,
    IssuePrediction,
    ResourceForecast,
    ObjectiveTrajectory
)
from anomaly_detector import (
    AnomalyDetector,
    Anomaly,
    AnomalyPattern
)
from optimizer import (
    OptimizationEngine,
    Optimization,
    OptimizationPlan
)

class TestPredictiveEngine(unittest.TestCase):
    """Test Predictive Analytics Engine"""
    
    def setUp(self):
        self.engine = PredictiveAnalyticsEngine()
        
    def test_phase_prediction_no_history(self):
        """Test phase prediction with no historical data"""
        prediction = self.engine.predict_phase_success('test_phase', {})
        
        self.assertIsInstance(prediction, PhasePrediction)
        self.assertEqual(prediction.phase_name, 'test_phase')
        self.assertGreater(prediction.success_probability, 0)
        self.assertLess(prediction.success_probability, 1)
        self.assertGreater(prediction.estimated_duration, 0)
        self.assertLess(prediction.confidence, 0.5)  # Low confidence without history
        
    def test_phase_prediction_with_history(self):
        """Test phase prediction with historical data"""
        # Record some history
        for i in range(10):
            self.engine.record_phase_execution(
                'test_phase',
                success=True,
                duration=300.0,
                context={'iteration': i}
            )
            
        prediction = self.engine.predict_phase_success('test_phase', {'iteration': 11})
        
        self.assertGreater(prediction.success_probability, 0.5)
        self.assertGreater(prediction.confidence, 0.3)
        
    def test_task_prediction(self):
        """Test task completion prediction"""
        prediction = self.engine.predict_task_completion(
            'test_task',
            complexity=0.5,
            dependencies=[]
        )
        
        self.assertIsInstance(prediction, TaskPrediction)
        self.assertEqual(prediction.task_id, 'test_task')
        self.assertGreater(prediction.completion_probability, 0)
        self.assertGreater(prediction.estimated_time, 0)
        
    def test_issue_prediction(self):
        """Test issue likelihood prediction"""
        # Record some issues
        for i in range(5):
            self.engine.record_issue(
                'syntax_error',
                'HIGH',
                {'file': f'test{i}.py'}
            )
            
        predictions = self.engine.predict_issue_likelihood('test_phase', {})
        
        self.assertIsInstance(predictions, list)
        if predictions:
            self.assertIsInstance(predictions[0], IssuePrediction)
            
    def test_resource_forecast(self):
        """Test resource requirement forecasting"""
        # Record some resource usage
        for i in range(10):
            self.engine.record_resource_usage(
                'test_phase',
                memory_mb=512.0,
                cpu_percent=50.0,
                duration=300.0
            )
            
        forecast = self.engine.forecast_resource_requirements('test_phase')
        
        self.assertIsInstance(forecast, ResourceForecast)
        self.assertGreater(forecast.estimated_memory_mb, 0)
        self.assertGreater(forecast.estimated_cpu_percent, 0)
        
    def test_objective_trajectory(self):
        """Test objective health trajectory prediction"""
        # Record objective states
        for i in range(10):
            self.engine.record_objective_state(
                'test_objective',
                'HEALTHY',
                {'tasks': 10, 'issues': 0}
            )
            
        trajectory = self.engine.predict_objective_trajectory('test_objective')
        
        self.assertIsInstance(trajectory, ObjectiveTrajectory)
        self.assertEqual(trajectory.objective_id, 'test_objective')
        self.assertIsNotNone(trajectory.current_health)
        
    def test_statistics(self):
        """Test engine statistics"""
        self.engine.record_phase_execution('phase1', True, 100, {})
        self.engine.record_task_completion('task1', True, 50, 0.5)
        self.engine.record_issue('error1', 'HIGH', {})
        
        stats = self.engine.get_statistics()
        
        self.assertIn('phases_tracked', stats)
        self.assertIn('tasks_tracked', stats)
        self.assertIn('issues_recorded', stats)
        self.assertEqual(stats['issues_recorded'], 1)

class TestAnomalyDetector(unittest.TestCase):
    """Test Anomaly Detection System"""
    
    def setUp(self):
        self.detector = AnomalyDetector(window_size=100)
        
    def test_phase_anomaly_detection(self):
        """Test phase execution anomaly detection"""
        # Record normal executions
        for i in range(20):
            self.detector.record_phase_metric(
                'test_phase',
                duration=300.0,
                success=True,
                context={}
            )
            
        # Record anomalous execution
        self.detector.record_phase_metric(
            'test_phase',
            duration=1500.0,  # 5x normal
            success=True,
            context={}
        )
        
        anomalies = self.detector.detect_phase_anomalies('test_phase')
        
        self.assertIsInstance(anomalies, list)
        # Should detect execution time anomaly
        
    def test_resource_anomaly_detection(self):
        """Test resource usage anomaly detection"""
        # Record normal usage
        for i in range(20):
            self.detector.record_resource_metric(
                'test_component',
                memory_mb=512.0,
                cpu_percent=50.0
            )
            
        # Record spike
        self.detector.record_resource_metric(
            'test_component',
            memory_mb=2048.0,  # 4x normal
            cpu_percent=95.0
        )
        
        anomalies = self.detector.detect_resource_anomalies('test_component')
        
        self.assertIsInstance(anomalies, list)
        
    def test_message_anomaly_detection(self):
        """Test message flow anomaly detection"""
        # Record normal message flow
        for i in range(20):
            self.detector.record_message_metric(
                message_count=100,
                message_types={'type1': 50, 'type2': 50}
            )
            
        # Record burst
        self.detector.record_message_metric(
            message_count=500,  # 5x normal
            message_types={'type1': 250, 'type2': 250}
        )
        
        anomalies = self.detector.detect_message_anomalies()
        
        self.assertIsInstance(anomalies, list)
        
    def test_objective_anomaly_detection(self):
        """Test objective health anomaly detection"""
        # Record healthy objective
        for i in range(10):
            self.detector.record_objective_metric(
                'test_objective',
                health_score=0.9,
                task_count=10,
                issue_count=0
            )
            
        # Record degradation
        self.detector.record_objective_metric(
            'test_objective',
            health_score=0.4,  # Significant drop
            task_count=10,
            issue_count=5
        )
        
        anomalies = self.detector.detect_objective_anomalies('test_objective')
        
        self.assertIsInstance(anomalies, list)
        
    def test_detect_all_anomalies(self):
        """Test comprehensive anomaly detection"""
        # Add various metrics
        self.detector.record_phase_metric('phase1', 300, True, {})
        self.detector.record_resource_metric('comp1', 512, 50)
        self.detector.record_message_metric(100, {'type1': 100})
        
        anomalies = self.detector.detect_all_anomalies()
        
        self.assertIsInstance(anomalies, list)
        
    def test_critical_anomalies(self):
        """Test critical anomaly filtering"""
        # Create some anomalies
        self.detector.detected_anomalies = [
            Anomaly(
                anomaly_type='test',
                severity='CRITICAL',
                description='Critical issue',
                detected_at=datetime.now(),
                affected_component='test'
            ),
            Anomaly(
                anomaly_type='test',
                severity='LOW',
                description='Minor issue',
                detected_at=datetime.now(),
                affected_component='test'
            )
        ]
        
        critical = self.detector.get_critical_anomalies()
        
        self.assertEqual(len(critical), 1)
        self.assertEqual(critical[0].severity, 'CRITICAL')
        
    def test_anomaly_summary(self):
        """Test anomaly summary generation"""
        self.detector.detected_anomalies = [
            Anomaly('type1', 'HIGH', 'desc', datetime.now(), 'comp1'),
            Anomaly('type2', 'MEDIUM', 'desc', datetime.now(), 'comp2')
        ]
        
        summary = self.detector.get_anomaly_summary()
        
        self.assertIn('total_anomalies', summary)
        self.assertIn('by_severity', summary)
        self.assertIn('by_type', summary)
        self.assertEqual(summary['total_anomalies'], 2)

class TestOptimizationEngine(unittest.TestCase):
    """Test Optimization Recommendations Engine"""
    
    def setUp(self):
        self.engine = OptimizationEngine()
        
    def test_performance_optimizations(self):
        """Test performance optimization generation"""
        # Record slow phase
        for i in range(20):
            self.engine.record_phase_performance(
                'slow_phase',
                duration=900.0,  # 15 minutes
                success=True
            )
            
        optimizations = self.engine.generate_performance_optimizations()
        
        self.assertIsInstance(optimizations, list)
        if optimizations:
            self.assertIsInstance(optimizations[0], Optimization)
            
    def test_resource_optimizations(self):
        """Test resource optimization generation"""
        # Record high memory usage
        for i in range(20):
            self.engine.record_resource_usage(
                'memory_hog',
                memory_mb=3072.0,  # 3GB
                cpu_percent=50.0
            )
            
        optimizations = self.engine.generate_resource_optimizations()
        
        self.assertIsInstance(optimizations, list)
        
    def test_quality_optimizations(self):
        """Test quality optimization generation"""
        # Record declining quality
        for i in range(10):
            value = 0.9 - (i * 0.05)  # Declining
            self.engine.record_quality_metric('test_quality', value)
            
        optimizations = self.engine.generate_quality_optimizations()
        
        self.assertIsInstance(optimizations, list)
        
    def test_scheduling_optimizations(self):
        """Test scheduling optimization generation"""
        # Record long tasks
        for i in range(20):
            self.engine.record_task_completion(
                'long_task',
                duration=2400.0  # 40 minutes
            )
            
        optimizations = self.engine.generate_scheduling_optimizations()
        
        self.assertIsInstance(optimizations, list)
        
    def test_strategic_optimizations(self):
        """Test strategic optimization generation"""
        metrics = {
            'completion_rate': 0.5,
            'avg_issue_resolution_time': 7200  # 2 hours
        }
        
        optimizations = self.engine.generate_strategic_optimizations(metrics)
        
        self.assertIsInstance(optimizations, list)
        
    def test_optimization_plan(self):
        """Test comprehensive optimization plan generation"""
        # Add some data
        self.engine.record_phase_performance('phase1', 600, True)
        self.engine.record_resource_usage('comp1', 2048, 80)
        
        plan = self.engine.generate_optimization_plan()
        
        self.assertIsInstance(plan, OptimizationPlan)
        self.assertIsNotNone(plan.plan_id)
        self.assertIsInstance(plan.optimizations, list)
        self.assertIsNotNone(plan.total_expected_benefit)
        self.assertIsNotNone(plan.implementation_timeline)
        
    def test_top_optimizations(self):
        """Test top optimizations retrieval"""
        # Add various optimizations
        for i in range(10):
            self.engine.record_phase_performance(f'phase{i}', 700, True)
            
        top = self.engine.get_top_optimizations(n=3)
        
        self.assertIsInstance(top, list)
        self.assertLessEqual(len(top), 3)
        
    def test_quick_wins(self):
        """Test quick win identification"""
        plan = self.engine.generate_optimization_plan()
        quick_wins = self.engine.get_quick_wins()
        
        self.assertIsInstance(quick_wins, list)
        # All should be low effort, high priority
        for opt in quick_wins:
            self.assertEqual(opt.implementation_effort, 'LOW')
            self.assertIn(opt.priority, ['HIGH', 'CRITICAL'])

class TestIntegration(unittest.TestCase):
    """Test integration between components"""
    
    def test_predictive_to_anomaly_flow(self):
        """Test data flow from predictive to anomaly detection"""
        predictor = PredictiveAnalyticsEngine()
        detector = AnomalyDetector()
        
        # Record data in predictor
        predictor.record_phase_execution('phase1', True, 300, {})
        
        # Use prediction in anomaly detection
        prediction = predictor.predict_phase_success('phase1', {})
        
        # Record actual execution
        detector.record_phase_metric('phase1', 300, True, {})
        
        # Both should work together
        self.assertIsNotNone(prediction)
        
    def test_anomaly_to_optimization_flow(self):
        """Test data flow from anomaly to optimization"""
        detector = AnomalyDetector()
        optimizer = OptimizationEngine()
        
        # Detect anomaly
        for i in range(20):
            detector.record_phase_metric('phase1', 300, True, {})
        detector.record_phase_metric('phase1', 1500, True, {})
        
        anomalies = detector.detect_phase_anomalies('phase1')
        
        # Generate optimizations based on anomaly
        optimizer.record_phase_performance('phase1', 1500, True)
        optimizations = optimizer.generate_performance_optimizations()
        
        # Should have optimizations if anomalies detected
        self.assertIsInstance(optimizations, list)
        
    def test_full_analytics_pipeline(self):
        """Test complete analytics pipeline"""
        predictor = PredictiveAnalyticsEngine()
        detector = AnomalyDetector()
        optimizer = OptimizationEngine()
        
        # 1. Record historical data
        for i in range(20):
            predictor.record_phase_execution('phase1', True, 300, {})
            detector.record_phase_metric('phase1', 300, True, {})
            optimizer.record_phase_performance('phase1', 300, True)
            
        # 2. Make prediction
        prediction = predictor.predict_phase_success('phase1', {})
        self.assertIsNotNone(prediction)
        
        # 3. Detect anomalies
        anomalies = detector.detect_all_anomalies()
        self.assertIsInstance(anomalies, list)
        
        # 4. Generate optimizations
        plan = optimizer.generate_optimization_plan()
        self.assertIsNotNone(plan)

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPredictiveEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAnomalyDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestOptimizationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)