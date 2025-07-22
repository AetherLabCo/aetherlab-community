# Changelog

All notable changes to the AetherLab SDK will be documented in this file.

## [0.3.1] - 2024-12-20

### Changed
- 📊 Updated all examples to explicitly show probability of non-compliance (`avg_threat_level`)
- 📝 Enhanced documentation to highlight the probability metrics
- 🎯 Made compliance metrics more prominent in all code examples

### Added
- ✨ Clear explanation that `avg_threat_level` represents probability of non-compliance (0-100%)
- 📈 Better visualization of risk metrics in examples

## [0.3.0] - 2024-12-20

### Added
- 🎉 Production PyPI release - now available via `pip install aetherlab`
- ✨ New `validate_content()` API with enhanced features:
  - Content type specification
  - Desired and prohibited attributes
  - Context support
  - Automatic violation detection
  - Suggested revisions for non-compliant content
- 🔧 Backward compatibility layer for legacy `test_prompt()` API
- 📝 Enhanced models with new fields for violations and suggestions
- 🚀 Full support for media analysis via `analyze_media()`
- 🔐 Enhanced watermarking via `add_secure_watermark()`

### Changed
- 📦 Moved from TestPyPI to production PyPI
- 🔄 Internal API calls now properly map between new and legacy formats
- 📚 Updated all documentation to use production installation
- 🎯 API responses now include more detailed compliance information

### Fixed
- 🐛 Fixed model attributes for new API compatibility
- 🔧 Corrected API authentication headers
- ✅ Enhanced error handling for better developer experience

## [0.2.1] - 2024-07-20
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