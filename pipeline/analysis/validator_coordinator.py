"""
Validator Coordinator

Coordinates all validation tools with a shared symbol table.
Eliminates duplicate work and enables cross-validator communication.
"""

from pathlib import Path
from typing import Dict, Optional
import logging
from datetime import datetime

from .symbol_table import SymbolTable
from .symbol_collector import SymbolCollector
from .type_usage_validator import TypeUsageValidator
from .method_existence_validator import MethodExistenceValidator
from .function_call_validator import FunctionCallValidator
from .enum_attribute_validator import EnumAttributeValidator
from .method_signature_validator import MethodSignatureValidator

# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace


class ValidatorCoordinator:
    """
    Coordinates all validation tools with shared data.
    
    Benefits:
    1. Collects all symbols once (classes, functions, types, calls)
    2. All validators share the same symbol table
    3. Eliminates duplicate AST parsing and data collection
    4. Enables cross-validator communication
    5. Provides unified error reporting
    
    Usage:
        coordinator = ValidatorCoordinator('/project')
        results = coordinator.validate_all()
        
        # Access individual results
        type_errors = results['type_usage']['errors']
        method_errors = results['method_existence']['errors']
    """
    
    def __init__(self, project_root: str, config_file: Optional[str] = None, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize validator coordinator.
        
        Args:
            project_root: Root directory of the project
            config_file: Optional path to validation config file
            logger: Optional logger instance
        """
        self.project_root = Path(project_root)
        self.config_file = config_file
        self.logger = logger or logging.getLogger(__name__)
        
        # Create shared symbol table
        self.symbol_table = SymbolTable(self.project_root)
        
        # Create symbol collector
        self.collector = SymbolCollector(self.symbol_table, self.logger)
        
        # Initialize validators
        # Note: All validators will be initialized after symbol collection
        self.type_validator = None  # Will be initialized with SymbolTable
        self.method_validator = None  # Will be initialized with SymbolTable
        self.call_validator = None  # Will be initialized with SymbolTable
        self.enum_validator = None  # Will be initialized with SymbolTable
        self.signature_validator = None  # Will be initialized with SymbolTable
        
        # Polytopic Integration
        self.message_bus = MessageBus()
        self.pattern_recognition = PatternRecognitionSystem(self.project_root)
        self.correlation_engine = CorrelationEngine()
        self.optimizer = OptimizationEngine()
        self.adaptive_prompts = AdaptivePromptSystem(
            self.project_root,
            self.pattern_recognition
        )
        self.dimensional_space = DimensionalSpace()
        
        # Validation tracking
        self.validation_count = 0
        self.validator_name = 'ValidatorCoordinator'
    
    def validate_all(self) -> Dict:
        """
        Run all validators with shared symbol table.
        
        Returns:
            Dict with results from all validators
        """
        self.logger.info("=" * 80)
        self.logger.info("COMPREHENSIVE CODE VALIDATION WITH SHARED SYMBOL TABLE")
        self.logger.info("=" * 80)
        self.logger.info(f"Project: {self.project_root}")
        self.logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("")
        
        # Phase 1: Collect all symbols
        self.logger.info("Phase 1: Collecting symbols...")
        self.collector.collect_from_project(self.project_root)
        
        stats = self.symbol_table.get_statistics()
        self.logger.info(f"  ✓ Collected {stats['total_classes']} classes")
        self.logger.info(f"  ✓ Collected {stats['total_functions']} functions")
        self.logger.info(f"  ✓ Collected {stats['total_methods']} methods")
        self.logger.info(f"  ✓ Collected {stats['total_enums']} enums")
        self.logger.info(f"  ✓ Built call graph with {stats['total_call_edges']} edges")
        self.logger.info("")
        
        # Initialize all validators with SymbolTable
        self.type_validator = TypeUsageValidator(str(self.project_root), self.config_file, self.symbol_table)
        self.method_validator = MethodExistenceValidator(str(self.project_root), self.config_file, self.symbol_table)
        self.call_validator = FunctionCallValidator(str(self.project_root), self.config_file, self.symbol_table)
        self.enum_validator = EnumAttributeValidator(str(self.project_root), self.symbol_table)
        self.signature_validator = MethodSignatureValidator(str(self.project_root), self.symbol_table)
        
        # Phase 2: Run validators
        self.logger.info("Phase 2: Running validators...")
        results = {}
        total_errors = 0
        
        # 1. Type Usage Validation
        self.logger.info("  1. Type Usage Validation...")
        result1 = self.type_validator.validate_all()
        results['type_usage'] = result1
        total_errors += result1['total_errors']
        self.logger.info(f"     ✓ {result1['total_errors']} errors found")
        
        # 2. Method Existence Validation
        self.logger.info("  2. Method Existence Validation...")
        result2 = self.method_validator.validate_all()
        results['method_existence'] = result2
        total_errors += result2['total_errors']
        self.logger.info(f"     ✓ {result2['total_errors']} errors found")
        
        # 3. Function Call Validation
        self.logger.info("  3. Function Call Validation...")
        result3 = self.call_validator.validate_all()
        results['function_calls'] = result3
        total_errors += result3['total_errors']
        self.logger.info(f"     ✓ {result3['total_errors']} errors found")
        
        # 4. Enum Attribute Validation
        self.logger.info("  4. Enum Attribute Validation...")
        result4 = self.enum_validator.validate_all()
        results['enum_attributes'] = result4
        total_errors += result4['total_errors']
        self.logger.info(f"     ✓ {result4['total_errors']} errors found")
        
        # 5. Method Signature Validation
        self.logger.info("  5. Method Signature Validation...")
        result5 = self.signature_validator.validate_all()
        results['method_signatures'] = result5
        total_errors += result5['total_errors']
        self.logger.info(f"     ✓ {result5['total_errors']} errors found")
        
        self.logger.info("")
        
        # Summary
        results['summary'] = {
            'total_errors': total_errors,
            'symbol_table_stats': stats,
            'duplicate_classes': self.symbol_table.get_duplicate_classes(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info("=" * 80)
        self.logger.info("VALIDATION COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Total errors: {total_errors}")
        self.logger.info("")
        
        return results
    
    def get_symbol_table(self) -> SymbolTable:
        """Get the shared symbol table."""
        return self.symbol_table
    
    def get_class_info(self, class_name: str, file: Optional[str] = None):
        """Get information about a class."""
        return self.symbol_table.get_class(class_name, file)
    
    def get_function_info(self, func_name: str):
        """Get information about a function."""
        return self.symbol_table.get_function(func_name)
    
    def get_variable_type(self, var_name: str, file: Optional[str] = None):
        """Get the type of a variable."""
        return self.symbol_table.get_variable_type(var_name, file)
    
    def get_callers(self, function: str):
        """Get all functions that call the given function."""
        return self.symbol_table.get_callers(function)
    
    def get_callees(self, function: str):
        """Get all functions called by the given function."""
        return self.symbol_table.get_callees(function)