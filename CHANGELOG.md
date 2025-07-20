# Changelog

All notable changes to the AetherLab Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2024-07-20

### Fixed
- Fixed API authentication header - now correctly uses `X-API-Key` instead of `Authorization: Bearer`
- Fixed compliance status parsing - now correctly checks for "Compliant" instead of "pass"
- Fixed confidence score calculation - now derived from `avg_threat_level` (confidence = 1 - threat_level)

### Added
- Added `avg_threat_level` field to `ComplianceResult` model
- Added comprehensive test suite and examples

### Changed
- Updated response parsing to match actual API response structure

## [0.1.1] - 2024-07-19

### Changed
- Updated API base URL from `https://api.aetherlab.ai` to `https://api.aetherlab.co`

### Fixed
- Fixed endpoint URL configuration

## [0.1.0] - 2024-07-19

### Added
- Initial release of AetherLab Python SDK
- Support for text prompt compliance testing
- Blacklist and whitelist keyword filtering
- Comprehensive error handling
- Full type hints and documentation
- Examples and quick start guide

### Features
- `AetherLabClient` for API interaction
- `test_prompt()` method for text compliance checking
- `test_image()` method for image compliance (placeholder)
- `add_watermark()` method for secure watermarking (placeholder)
- Custom exception classes for better error handling
- Data models for API responses 