"""Unit tests for the migration engine."""

import pytest
import os
import tempfile
from pathlib import Path

from migrations.engine.migration_engine import OdooMigrationEngine, MigrationReport
from migrations.transformers.constants import SUPPORTED_VERSIONS


class TestMigrationReport:
    """Test MigrationReport class."""

    def test_create_report(self):
        """Test creating a migration report."""
        report = MigrationReport('test_module', '14.0', '15.0')
        assert report.module_name == 'test_module'
        assert report.from_version == '14.0'
        assert report.to_version == '15.0'
        assert report.status == 'pending'

    def test_add_change(self):
        """Test adding changes to report."""
        report = MigrationReport('test_module', '14.0', '15.0')
        report.add_change('file.py', 'python', {'old': 'code', 'new': 'code2'})

        assert len(report.changes) == 1
        assert report.changes[0]['file'] == 'file.py'

    def test_add_error(self):
        """Test adding errors to report."""
        report = MigrationReport('test_module', '14.0', '15.0')
        report.add_error('Test error', 'file.py')

        assert len(report.errors) == 1
        assert report.errors[0]['message'] == 'Test error'

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = MigrationReport('test_module', '14.0', '15.0')
        report.add_change('file.py', 'python', {'change': 'test'})

        report_dict = report.to_dict()
        assert report_dict['module'] == 'test_module'
        assert report_dict['summary']['total_changes'] == 1


class TestOdooMigrationEngine:
    """Test OdooMigrationEngine class."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = OdooMigrationEngine(target_version='19.0')
        assert engine.target_version == '19.0'
        assert 'python_transformer' in dir(engine)

    def test_supported_versions(self):
        """Test supported versions."""
        engine = OdooMigrationEngine()
        assert '14.0' in SUPPORTED_VERSIONS
        assert '19.0' in SUPPORTED_VERSIONS

    def test_migrate_invalid_source_version(self):
        """Test migration with invalid source version."""
        engine = OdooMigrationEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = engine.migrate_module(tmpdir, '13.0', '15.0')
            assert report.status == 'failed'
            assert len(report.errors) > 0

    def test_migrate_invalid_target_version(self):
        """Test migration with invalid target version."""
        engine = OdooMigrationEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = engine.migrate_module(tmpdir, '14.0', '20.0')
            assert report.status == 'failed'
            assert len(report.errors) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
