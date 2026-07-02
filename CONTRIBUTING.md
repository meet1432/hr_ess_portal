# Contributing to Employee Self-Service Portal

Thank you for your interest in contributing! We welcome contributions from the community.

## Code of Conduct

Please be respectful and constructive in all interactions. We're committed to providing a welcoming environment for all contributors.

## How to Contribute

### Reporting Issues

1. **Check existing issues** - Search to see if your issue is already reported
2. **Provide details** - Include:
   - Odoo version
   - Module version
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Error logs/tracebacks

### Suggesting Features

1. **Describe the use case** - Explain why this feature is needed
2. **Provide examples** - Show how it would be used
3. **Consider impact** - Will it affect security or performance?

### Submitting Code

#### Setup
```bash
# Clone the repository
git clone https://github.com/meet1432/hr-ess-portal.git
cd hr-ess-portal

# Create a branch
git checkout -b feature/your-feature-name

# Make changes and test
# ...
```

#### Code Standards

**Python Code**
- Follow PEP 8 style guide
- Use type hints where applicable
- Add docstrings to functions
- Keep functions focused and testable
- Handle exceptions properly

```python
def example_function(param: str) -> dict:
    """
    Brief description of what this does.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    try:
        # Implementation
        pass
    except Exception as exc:
        _logger.warning('Operation failed: %s', exc)
        raise UserError('User-friendly error message')
```

**JavaScript Code**
- Use ES6+ syntax
- Attach functions to `window` for onclick handlers
- Use meaningful variable names
- Add comments for complex logic
- Handle errors gracefully

```javascript
window.functionName = function(param) {
    // Validate input
    if (!param || param.length === 0) {
        alert('Please provide a valid value');
        return;
    }
    
    // Implementation
    fetch('/endpoint', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({data: param})
    })
    .then(r => r.json())
    .then(data => {
        if (data.result) {
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(e => alert('Request failed: ' + e.message));
};
```

**XML/Templates**
- Use proper indentation (4 spaces)
- Escape special characters in JavaScript
- Use CDATA sections for complex code
- Add descriptive comments for templates

```xml
<template id="template_name" name="Template Name">
    <!-- Section description -->
    <div class="container">
        <t t-foreach="items" t-as="item">
            <div t-att-data-id="item.id">
                <t t-esc="item.name"/>
            </div>
        </t>
    </div>
</template>
```

#### Commit Messages

- Use clear, descriptive messages
- Start with verb: "Add", "Fix", "Update", "Refactor", "Remove"
- Keep first line under 70 characters
- Add detailed explanation if needed

```
Add timesheet validation for negative hours

- Prevent creation of entries with negative unit_amount
- Show user-friendly error message
- Add validation in both backend and frontend
```

#### Testing

1. **Manual testing**
   ```bash
   # Test in a local Odoo instance
   # - Create test employee with portal access
   # - Test each module's main workflows
   # - Test with different user roles
   ```

2. **Security testing**
   - Verify users see only their own records
   - Test access control rules
   - Try accessing other users' data (should fail)

3. **Browser compatibility**
   - Test in Chrome, Firefox, Safari
   - Test on mobile devices
   - Check responsive design

#### Pull Request Process

1. **Update documentation**
   - Update README.md if needed
   - Add to CHANGELOG.md under "Unreleased"
   - Update __manifest__.py if dependencies changed

2. **Create PR with**
   - Clear title: "Add X", "Fix Y"
   - Description of changes
   - Testing notes
   - Any breaking changes

3. **PR Template**
   ```markdown
   ## Description
   Brief description of what this PR does.
   
   ## Changes
   - Change 1
   - Change 2
   
   ## Testing
   - [ ] Manual testing completed
   - [ ] Security implications reviewed
   - [ ] No breaking changes
   
   ## Screenshots (if applicable)
   Include before/after or workflow screenshots
   ```

### Development Guidelines

#### Security
- Always sanitize user input
- Use `sudo()` carefully - only for portal data
- Validate user permissions on backend
- Escape HTML/JavaScript in templates
- Use CSRF tokens for all AJAX calls

#### Performance
- Use `search()` with proper limits
- Avoid N+1 queries with proper domain filters
- Cache results when appropriate
- Use indexes for frequently filtered fields

#### Code Organization
- Keep controllers focused (one responsibility)
- Group related views in templates
- Use meaningful variable/function names
- Extract common logic to utilities

## Project Structure

```
hr_ess_portal/
├── controllers/       # HTTP routes and business logic
├── models/           # Database models and extensions
├── views/            # Portal templates
├── static/src/       # CSS and JavaScript
├── security/         # Access control rules
├── data/             # Portal menu items
└── wizard/           # Multi-step workflows
```

## Running Locally

### Prerequisites
- Odoo 19 Enterprise Edition
- Python 3.8+
- PostgreSQL 12+

### Installation

```bash
# Clone the repo
git clone https://github.com/meet1432/hr-ess-portal.git

# Copy to Odoo addons
cp -r hr_ess_portal /path/to/odoo/addons/

# Restart Odoo and install module
```

### Testing Changes

```bash
# In Odoo:
# 1. Enable developer mode
# 2. Go to Apps → Update Apps List
# 3. Search for "Employee Self-Service Portal"
# 4. Click Install or Upgrade
# 5. Test your changes in the portal
```

## Documentation

### Updating README
- Add feature descriptions
- Update API endpoint lists
- Include installation steps
- Provide usage examples

### Adding Docstrings
```python
def method_name(self, param):
    """
    One-line summary.
    
    Longer description if needed.
    
    Args:
        param: Description
        
    Returns:
        Description
        
    Raises:
        UserError: When validation fails
    """
```

## Review Process

1. Maintainers will review within 5-7 days
2. We may ask for changes or clarifications
3. Once approved, your PR will be merged
4. You'll be added to CONTRIBUTORS.md

## Questions?

- Open a [GitHub Discussion](https://github.com/meet1432/hr-ess-portal/discussions)
- Check existing issues for similar questions
- Review documentation in README.md

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- GitHub contributors graph
- Release notes for their contributions

Thank you for making this project better! 🎉